# cad-coder-nextgen: Fine-tuning and Deploying Large-Scale Vision Language Models for CAD Code Generation

## Milestone2: AC215 CAD-Coder Project MS2 Documentation: Please see the detailed markdown file located in the src/datapipeline folder titled "milestone2.md" as your starting point.

## Milestone3: AC215 CAD-Coder Project MS3 Documentation: Please see the detailed markdown file located in the src/ui folder titled "ui.md" to learn about the additional modifications (added a containerized React UI) we made from Milestone2. Additionally, you can find our midterm MS3 presentation slides here: [https://drive.google.com/file/d/1zJa326zX9a0zp4HBTscuqiaStooRAZat/view?usp=sharing](https://drive.google.com/file/d/1zJa326zX9a0zp4HBTscuqiaStooRAZat/view?usp=sharing)


## Milestone4: Development and Deployment Preparation


Project Team Members: Yuyan Fan, Jing Xu, Frank Chen, Aditya Palaparthi
Group Name: CAD-Coder

Project:

Computer-Aided Design (CAD) is essential to engineering and
manufacturing, yet creating CAD models remains slow and expertise-driven. Recent advances in
vision-language models (VLMs) offer a chance to accelerate and democratize CAD workflows. Our
project builds on CAD-Coder, an open-source model that converts text and images into CadQuery
Python code. While promising, CAD-Coder has not been systematically evaluated across model scales or
deployed in an accessible interface. We will close this gap by fine-tuning scaled variants, analyzing
performance trends, and deploying them in a chatbot that enables engineers, students, and hobbyists to
generate CAD code interactively. Compared to manual modeling, proprietary CAD tools, or limited AI
plugins, our system lowers barriers to entry, speeds iteration, and contributes new insights into
multimodal model scaling. Our team brings strong data science expertise, including research experience at
MIT on generative AI and 3D engineering design, positioning us well to execute this project.

We aim to design and deploy a scalable chatbot system that generates CAD code from text and/or image inputs, while studying how performance scales across model sizes.

Scope and Objectives: Our project scope is to deploy a research-informed CAD chatbot. Namely:
1. Scaling Analysis
- Fine-tune Qwen-2.5 models (3B, 7B, 14B, 32B, 72B) on the GenCAD dataset and analyze scaling trends in accuracy, efficiency, and robustness.
2. Deployment
- Deploy two models on Google Cloud VertexAI: Original CAD-Coder (LLaV A baseline) and best fine-tuned Qwen-2.5 variant
3. Chatbot Interface
- Build a ChatGPT-style interface with text input + image upload, model selection dropdown, chat history, and Retrieval-Augmented Generation (RAG)
4. Efficient Inference
- Implement optimized pipelines (quantization, FlashAttention, continuous batching,
multi-GPU scheduling) to ensure practical latency and scalability.

Users will include mechanical engineers for rapidly prototyping CAD components, students &
educators for having an accessible entry point for learning CAD, and makers & hobbyists for
generating parts without mastering complex CAD software. Benefits over Alternatives: Unlike
commercial CAD tools or plugins, our system automates code generation directly from natural inputs
(text/images), provides open, reproducible research into model scaling, and offers a flexible,
cloud-deployed interface for broader accessibility.
