# Milestone 2

Team Members: Yuyan Fan, Jing Xu, Frank Chen, Aditya Palaparthi

_________________________________________

## 1. Virtual Environment Setup
## 🐳 Google Cloud Compute Engine VM Setup for Docker Containers

This document provides the step-by-step instructions for creating a Google Cloud Compute Engine Virtual Machine (VM) and installing the Docker Engine runtime. This configuration establishes a virtual environment capable of supporting containers for deploying applications like the CAD-Coder or Qwen-2.5 models.

---

## 1. Create and Configure the Compute Engine VM

### 1.1 Provision the VM Instance

1.  Navigate to the **Compute Engine** $\rightarrow$ **VM Instances** page in the Google Cloud Console.
2.  Click **CREATE INSTANCE**.
3.  Configure the following key parameters for the VM, based on the deployed instance:
    * **Name:** `cad-coder-container-vm`
    * **Region/Zone:** `us-central1-c`
    * **Machine configuration:** (Selected based on project requirements, e.g., **E2-series**).
    * **Boot Disk:**
        * **Operating System:** **Ubuntu** (as used in the installation screenshots).
        * **Size and Type:** Default persistent disk size (e.g., **10 GB** or similar default size for Ubuntu standard images).
    * **Firewall:** Ensure **Allow HTTP traffic** and **Allow HTTPS traffic** are checked (if needed).
4.  Click **CREATE**.
5.  **Verify the VM status:** Confirm the instance, `cad-coder-container-vm`, is in the **Running** state.

Screenshot location: /docs/screenshots/milestone2.1_helloworld.png
![Google Cloud VM Instance List showing cad-coder-container-vm is Running](docs/screenshots/milestone2.1_helloworld.png "Instance Running:")

---

## 2. Install and Configure Docker Engine

### 2.1 Connect via SSH

1.  On the VM Instances page, locate the `cad-coder-container-vm` instance.
2.  Click the **SSH** button next to the instance name to open a browser-based terminal connection.

### 2.2 Install and Start Docker Engine

The following commands (appropriate for **Ubuntu** systems) ensure the Docker Engine is installed and running correctly.

1.  **Start and enable the Docker service:**
    ```bash
    sudo systemctl start docker
    sudo systemctl enable docker
    ```

---

## 3. Verify Docker Functionality

Execute the `hello-world` container to confirm that Docker is correctly installed, can pull images, and can run containers successfully.

1.  **Run the test container:**
    ```bash
    sudo docker run hello-world
    ```
    * **Confirmation:** The output confirms that the Docker installation appears to be working correctly, having pulled the `hello-world:latest` image and executed the container.

Screenshot location:
/docs/screenshots/milestone2.1_helloworld.png
![SSH terminal showing Docker run hello-world command and successful output](docs/screenshots/milestone2.1_helloworld.png "Docker Hello-World Run:")

2.  **Verify container execution and status:**
    ```bash
    sudo docker ps -a
    ```
    * **Confirmation:** The `hello-world` container is listed with a **STATUS** of `Exited (0)`. This confirms successful execution and completion.

Screenshot location:
/docs/screenshots/milestone2.1_psa.png
![SSH terminal showing the output of sudo docker ps -a](docs/screenshots/milestone2.1_psa.png "Docker Container Exited Status:")

---

## 4. Next Steps

The `cad-coder-container-vm` environment is fully configured and verified to support container deployment. The next phase involves:

* Building or pulling the container image for the **CAD-Coder** or **Qwen-2.5** application.
* Running the application container on this VM instance.
_________________________________________
## 2. END-TO-END CONTAINERIZED PIPELINE
Please see documentation starting with the milestone2.2_endtoend.md file.

_________________________________________
## 3. Teams using LLMs (Implement a RAG pipeline)
Please see documentation starting with the milestone2.3_rag.md file in the subfolder rag starting from this folder.



_________________________________________

## 5. Application Mock-Up
Preliminary Design: System components will include a frontend for a chatbot with multimodal input and model selection, a backend for VertexAI-managed inference pipelines for scalable serving, and CI/CD for deployment with Docker + Kubernetes. Our mockup is a ChatGPT-style chat window with file upload, dropdown to switch models, and RAG-backed history. Here is the link to our public Figma design: [https://casual-lion-94885387.figma.site/](https://casual-lion-94885387.figma.site/)