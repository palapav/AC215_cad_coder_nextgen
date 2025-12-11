"""
Load Testing for CAD-Coder Application

This Locust file defines load testing scenarios for the CAD-Coder application,
including the backend API and model inference endpoints.

Usage:
    # Run locally
    locust -f locustfile.py --host=http://localhost:8000
    
    # Run with web UI
    locust -f locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0
    
    # Run headless
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m
    
    # Run distributed (master)
    locust -f locustfile.py --master --host=http://localhost:8000
    
    # Run distributed (worker)
    locust -f locustfile.py --worker --master-host=<master-ip>

Environment Variables:
    LOCUST_HOST: Target host URL
    LOCUST_USERS: Number of users to simulate
    LOCUST_SPAWN_RATE: Users spawned per second
    LOCUST_RUN_TIME: Test duration (e.g., "5m", "1h")
"""

import base64
import io
import json
import logging
import os
import random
import time
from typing import Optional

from locust import HttpUser, task, between, events, tag
from locust.runners import MasterRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Test Data
# =============================================================================

# Sample prompts for CAD generation
SAMPLE_PROMPTS = [
    "Generate CADQuery code for a simple cube with dimensions 10x10x10",
    "Create a cylindrical shape with radius 5 and height 20",
    "Design a bracket with two mounting holes",
    "Generate a gear with 20 teeth",
    "Create a box with rounded corners",
    "Design a pipe fitting with internal threads",
    "Generate a simple washer with outer diameter 30mm",
    "Create a rectangular plate with 4 corner holes",
    "Design a hex nut",
    "Generate a simple L-bracket",
]

# Sample base64 encoded test image (1x1 black pixel PNG)
# In production, use actual CAD images
SAMPLE_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def generate_test_image(size: int = 336) -> str:
    """Generate a random test image as base64."""
    try:
        from PIL import Image
        import numpy as np
        
        # Create a random grayscale image
        arr = np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)
        img = Image.fromarray(arr, 'RGB')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except ImportError:
        # Fallback to minimal test image
        return SAMPLE_IMAGE_B64


# =============================================================================
# User Behaviors
# =============================================================================

class CADCoderUser(HttpUser):
    """
    Simulates a typical CAD-Coder user browsing and generating CAD code.
    """
    
    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """Called when a user starts."""
        self.test_image = generate_test_image()
        logger.info(f"User started: {self.client.base_url}")
    
    @task(10)
    @tag("health")
    def health_check(self):
        """Check service health (high frequency)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    @tag("api")
    def root_endpoint(self):
        """Hit the root endpoint."""
        self.client.get("/")
    
    @task(3)
    @tag("inference", "qwen")
    def generate_cad_qwen_text_only(self):
        """Generate CAD code using Qwen with text-only prompt."""
        prompt = random.choice(SAMPLE_PROMPTS)
        
        payload = {
            "prompt": prompt,
            "model_choice": "qwen",
            "image": None,
        }
        
        with self.client.post(
            "/generate_cad",
            json=payload,
            catch_response=True,
            timeout=120,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "cad_code" in data:
                    response.success()
                else:
                    response.failure("Missing cad_code in response")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Error: {response.status_code}")
    
    @task(2)
    @tag("inference", "qwen", "image")
    def generate_cad_qwen_with_image(self):
        """Generate CAD code using Qwen with image."""
        prompt = "Generate the CADQuery code for the CAD model shown in the image."
        
        payload = {
            "prompt": prompt,
            "model_choice": "qwen",
            "image": f"data:image/png;base64,{self.test_image}",
        }
        
        with self.client.post(
            "/generate_cad",
            json=payload,
            catch_response=True,
            timeout=180,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "cad_code" in data:
                    response.success()
                else:
                    response.failure("Missing cad_code in response")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Error: {response.status_code}")
    
    @task(2)
    @tag("inference", "llava", "image")
    def generate_cad_llava(self):
        """Generate CAD code using LLaVA with image."""
        prompt = "Generate the CadQuery code needed to create the CAD for the provided image."
        
        payload = {
            "prompt": prompt,
            "model_choice": "llava",
            "image": f"data:image/png;base64,{self.test_image}",
        }
        
        with self.client.post(
            "/generate_cad",
            json=payload,
            catch_response=True,
            timeout=180,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "cad_code" in data:
                    response.success()
                else:
                    response.failure("Missing cad_code in response")
            elif response.status_code == 503:
                response.failure("Service unavailable")
            else:
                response.failure(f"Error: {response.status_code}")
    
    @task(1)
    @tag("history")
    def get_history(self):
        """Retrieve generation history."""
        with self.client.get(
            "/history",
            params={"limit": 10},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Error: {response.status_code}")


class HeavyInferenceUser(HttpUser):
    """
    Simulates a power user making many inference requests.
    Used for stress testing the GPU inference services.
    """
    
    wait_time = between(0.5, 2)
    weight = 1  # Lower weight than CADCoderUser
    
    def on_start(self):
        """Called when a user starts."""
        self.test_image = generate_test_image(512)  # Larger image
    
    @task(5)
    @tag("stress", "qwen")
    def stress_qwen(self):
        """Stress test Qwen inference."""
        prompt = random.choice(SAMPLE_PROMPTS) + " Make it detailed with precise dimensions."
        
        payload = {
            "prompt": prompt,
            "model_choice": "qwen",
            "image": f"data:image/png;base64,{self.test_image}",
        }
        
        with self.client.post(
            "/generate_cad",
            json=payload,
            catch_response=True,
            timeout=300,
            name="/generate_cad [stress-qwen]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error: {response.status_code}")
    
    @task(3)
    @tag("stress", "llava")
    def stress_llava(self):
        """Stress test LLaVA inference."""
        prompt = "Generate detailed CADQuery code for this complex CAD model."
        
        payload = {
            "prompt": prompt,
            "model_choice": "llava",
            "image": f"data:image/png;base64,{self.test_image}",
        }
        
        with self.client.post(
            "/generate_cad",
            json=payload,
            catch_response=True,
            timeout=300,
            name="/generate_cad [stress-llava]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error: {response.status_code}")


# =============================================================================
# Event Handlers
# =============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("=" * 50)
    logger.info("CAD-Coder Load Test Starting")
    logger.info(f"Target host: {environment.host}")
    logger.info("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("=" * 50)
    logger.info("CAD-Coder Load Test Complete")
    
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Avg response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Requests/sec: {stats.total.current_rps:.2f}")
    logger.info("=" * 50)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on every request (for custom logging/metrics)."""
    if exception:
        logger.warning(f"Request failed: {name} - {exception}")


# =============================================================================
# Custom Load Shape (Optional)
# =============================================================================

class StagesShape:
    """
    Custom load shape that ramps up and down in stages.
    Useful for testing autoscaling behavior.
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},    # Warm-up
        {"duration": 120, "users": 50, "spawn_rate": 5},   # Ramp up
        {"duration": 180, "users": 100, "spawn_rate": 10}, # Peak load
        {"duration": 120, "users": 50, "spawn_rate": 5},   # Ramp down
        {"duration": 60, "users": 10, "spawn_rate": 2},    # Cool down
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
            run_time -= stage["duration"]
        
        return None


# Uncomment to use staged load shape
# class StagedCADCoderUser(CADCoderUser, StagesShape):
#     pass
