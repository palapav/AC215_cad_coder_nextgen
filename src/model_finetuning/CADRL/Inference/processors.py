import os
import tempfile
from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from tqdm.auto import tqdm
import numpy as np
import tabulate
from contextlib import redirect_stdout, redirect_stderr
import sys
from contextlib import contextmanager
import json

TEST_TEMPLATE = """
{code}
cq.exporters.export(solid, {file_name})
"""

OCC_IOU_TEMPLATE = """
from Inference.Geom._OCC_IOU import align_shapes, load_step_file

solid_gt = load_step_file("{ground_truth_step_path}")
solid_gen = load_step_file("{generated_step_path}")

IOU = align_shapes(solid_gen, solid_gt)[1]
"""

@contextmanager
def suppress_output_os():

    # Ensure this runs only on non-Windows platforms
    if sys.platform == "win32":
        yield
        return

    stdout_fd = 1
    stderr_fd = 2
    
   
    saved_stdout_fd = os.dup(stdout_fd)
    saved_stderr_fd = os.dup(stderr_fd)
    
    devnull_fd = os.open(os.devnull, os.O_RDWR)
    
    try:
        os.dup2(devnull_fd, stdout_fd)
        os.dup2(devnull_fd, stderr_fd)
        yield
    finally:
        os.dup2(saved_stdout_fd, stdout_fd)
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(saved_stdout_fd)
        os.close(saved_stderr_fd)
        os.close(devnull_fd)
        
@contextmanager
def suppress_output():
    with redirect_stdout(open(os.devnull, 'w')), redirect_stderr(open(os.devnull, 'w')):
        yield

def _get_iou(gt_code, gen_code, gt_file, gen_file, queue):
    with suppress_output_os():
        with suppress_output():
            try:
                exec(TEST_TEMPLATE.format(code=gt_code, file_name=f'"{gt_file.name}"'))
                
            except Exception as e:
                queue.put((-1, 1))
                return

            try:
                exec(TEST_TEMPLATE.format(code=gen_code, file_name=f'"{gen_file.name}"'))
            except Exception as e:
                queue.put((-1, 2))
                return
            
            try:
                
                local_vars = {}
                exec_globals = {'__builtins__': __builtins__}

                exec(OCC_IOU_TEMPLATE.format(
                    ground_truth_step_path=gt_file.name,
                    generated_step_path=gen_file.name
                ),exec_globals, local_vars)
                
                iou = local_vars.get('IOU', -1.0)
                queue.put((iou, 0))
                return
            
            except Exception as e:
                queue.put((-1, 3))
                return

class IOUProcessor:
    def __init__(self, num_workers=64, timeout=15, heal_failed=True, quiet=False):
        self.num_workers = num_workers
        self.timeout = timeout
        self.heal_failed = heal_failed
        self.quiet = quiet

    def __call__(self, response):
        if isinstance(response, dict):
            return self._run(response, timeout=self.timeout, heal_failed=self.heal_failed)
        elif isinstance(response, list):
            return self._run_parallel(response)

    @staticmethod
    def _run(response, timeout=30, heal_failed=True):
        gt_code = response['ground_truth']
        gen_code = response['generated']
        gt_file = tempfile.NamedTemporaryFile(suffix=".step", delete=True)
        gen_file = tempfile.NamedTemporaryFile(suffix=".step", delete=True)
        queue = Queue()
        process = Process(target=_get_iou, args=(gt_code, gen_code, gt_file, gen_file, queue))
        process.start()
        
        try:
            result = queue.get(timeout=timeout)
        except Exception as e:
            process.kill()
            result = (-1, 4)
            
        gt_file.close()
        gen_file.close()
        
        if result[0] > 1.0 and heal_failed:
            result = (-1, 5)
        
        return result
    
    def _run_parallel(self, completions):
        iou_func = partial(self._run, timeout=self.timeout, heal_failed=self.heal_failed)

        ordered_results = [None] * len(completions)

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_index = {
                executor.submit(iou_func, c): i 
                for i, c in enumerate(completions)
            }
            
            if not self.quiet:
                for future in tqdm(as_completed(future_to_index), total=len(completions)):
                    try:
                        index = future_to_index[future]
                        result = future.result()
                        ordered_results[index] = result
                    except Exception as e:
                        index = future_to_index[future]
                        ordered_results[index] = (-1, 6)
                        
            else:
                for future in as_completed(future_to_index):
                    try:
                        index = future_to_index[future]
                        result = future.result()
                        ordered_results[index] = result
                    except Exception as e:
                        index = future_to_index[future]
                        ordered_results[index] = (-1, 6)
                    
        ious = []
        statuses = []
        for iou, status in ordered_results:
            ious.append(iou)
            statuses.append(status)

        ious = np.array(ious)
        statuses = np.array(statuses, dtype=int)

        return ious, statuses
        
    def parse_results(self, ious, status_codes, verbose=True):
        summary = {
            'Valid IOU Mean': np.mean(ious[status_codes == 0]),
            'Valid IOU Median': np.median(ious[status_codes == 0]),
            'Valid IOU STD': np.std(ious[status_codes == 0]),
            'VSR': np.mean(status_codes == 0),
            'Adjusted IOU Mean': np.mean(np.where(status_codes == 0, ious, 0)),
            'Adjusted IOU Median': np.median(np.where(status_codes == 0, ious, 0)),
            'Adjusted IOU STD': np.std(np.where(status_codes == 0, ious, 0)),
            'Num Failed GT': np.sum(status_codes == 1),
            'Num Failed Gen': np.sum(status_codes == 2),
            'Num Failed OCC': np.sum(status_codes == 3),
            'Num Timeouts': np.sum(status_codes == 4),
            'Num None Solids': np.sum(status_codes == 5),
            'Num Failed Processing': np.sum(status_codes == 6)
        }
        
        if verbose:
            print("IOU Summary:")
            print(tabulate.tabulate(
                summary.items(),
                headers=['Metric', 'Value'],
                tablefmt='grid'
            ))
        
        return summary
    
    def save_results(self, ious, status_codes, output_file='experiment_results.json'):
        
        out = {"Summary": self.parse_results(ious, status_codes, verbose=False),
               "results": []}
        
        Errors = {
            1: "Ground Truth Reconstruction Failed",
            2: "Generated Code Failed",
            3: "OCC Computation Failed",
            4: "OCC Timeout",
            5: "None Solid Geometry Present",
            6: "Multiprocessing Error"
        }
        
        for i, (iou, status) in enumerate(zip(ious, status_codes)):
            out["results"].append({
                "Index": i,
                "IoU": iou if iou >= 0 else "N/A",
                "Status": Errors.get(status, "Unknown Error")
            })
            
        with open(output_file, 'w') as f:
            json.dump(out, f, indent=4)
        
        print(f"Results saved to {output_file}")