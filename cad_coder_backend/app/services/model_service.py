import asyncio

async def generate_cad_code(prompt: str, image=None):
    """
    Dummy model function for CAD code generation.
    Replace this with actual VLM inference later.
    """
    await asyncio.sleep(1)
    code = (
        "import cadquery as cq\n"
        f"result = cq.Workplane('XY').box(1,1,1)  # generated for: {prompt}\n"
    )
    return code
