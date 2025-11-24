# CAD-Coder UI - React Interface Documentation

> **🚀 Quick Start:** Run `./docker-run.sh rebuild` in the `src/ui/` directory, then access the UI at `http://localhost:8080`

---

## Overview

This is the **AI Model Sandbox Interface** for the CAD-Coder project, built with React, TypeScript, and Vite. The UI provides a modern, multimodal chat interface inspired by ChatGPT, allowing users to interact with AI models for CAD code generation tasks. It features model selection, chat history management, and support for both text and image inputs.

---

## Architecture & Technology Stack

### Core Technologies
- **React 18.3.1**: Modern UI library with hooks for state management
- **TypeScript**: Type-safe JavaScript development
- **Vite 6.3.5**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework (via globals.css)

### UI Component Library
- **Radix UI**: Comprehensive set of accessible, unstyled UI primitives including:
  - Dialog, Dropdown Menu, Select, Tabs, Tooltip
  - Accordion, Avatar, Button, Card, Input
  - Progress, Scroll Area, Separator, Switch
  - And many more (see `package.json` for full list)
- **Lucide React**: Icon library
- **Next Themes**: Dark/light mode theming support

### Additional Libraries
- **React Hook Form**: Form state management
- **Recharts**: Data visualization (if needed for future features)
- **Embla Carousel**: Carousel/slider functionality
- **cmdk**: Command menu component
- **Sonner**: Toast notifications

---

## Project Structure

```
src/ui/
├── Dockerfile                  # Multi-stage Docker build configuration
├── .dockerignore              # Docker build exclusion rules
├── package.json               # Project dependencies and scripts
├── vite.config.ts             # Vite configuration with path aliases
├── index.html                 # HTML entry point
├── src/
│   ├── main.tsx              # React app entry point
│   ├── App.tsx               # Root component (renders AIModelSandbox)
│   ├── index.css             # Global styles
│   ├── styles/
│   │   └── globals.css       # Tailwind CSS and custom styles
│   ├── components/
│   │   ├── AIModelSandbox.tsx     # Main chat interface component
│   │   ├── ModelSelector.tsx      # AI model selection dropdown
│   │   ├── ChatHistory.tsx        # Message history display
│   │   ├── ChatInput.tsx          # User input with file upload
│   │   ├── ChatMessage.tsx        # Individual message component
│   │   ├── ChatSidebar.tsx        # Session management sidebar
│   │   ├── ui/                    # Reusable UI primitives (Radix wrappers)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   └── ... (30+ components)
│   │   └── ImageWithFallback.tsx  # Image handling component
│   ├── guidelines/
│   │   └── Guidelines.md      # Design guidelines
│   └── Attributions.md        # Third-party attributions
└── ui.md                      # This documentation file
```

---

## Key Components Description

### 1. **AIModelSandbox.tsx** (Main Application)
The central component orchestrating the entire chat interface:
- **Model Selection**: Allows users to switch between AI models (Baseline-LLaVA, Qwen-2.5-xB)
- **Session Management**: Create, delete, and switch between chat sessions
- **Message Handling**: Processes user input (text + images) and generates mock AI responses
- **State Management**: Uses React hooks (`useState`) to manage sessions, messages, and UI state
- **Multimodal Support**: Detects and responds differently when images are uploaded

**Key Features:**
- Mock AI responses for demonstration (no backend integration yet)
- Different response patterns for text-only vs. multimodal queries
- Session persistence during the current browser session

### 2. **ModelSelector.tsx**
Dropdown component for selecting the active AI model:
- **Baseline-LLaVA**: Vision-language model for multimodal tasks
- **Qwen-2.5-xB**: Advanced reasoning and code generation model

### 3. **ChatHistory.tsx**
Displays the conversation history with:
- User messages (text + attached images)
- AI assistant responses
- Timestamps
- Scrollable message container

### 4. **ChatInput.tsx**
User input interface featuring:
- Text area for message composition
- File upload button for images (supports multimodal queries)
- Send button
- Loading state during AI response generation

### 5. **ChatSidebar.tsx**
Session management sidebar providing:
- List of all chat sessions
- Session creation button
- Session deletion
- Active session highlighting

### 6. **UI Components** (`components/ui/`)
A comprehensive library of 30+ reusable, accessible UI primitives built on Radix UI, including buttons, inputs, dialogs, dropdowns, tooltips, and more. These components ensure:
- **Accessibility**: ARIA compliant, keyboard navigable
- **Customizability**: Styled with Tailwind CSS
- **Consistency**: Unified design language across the app

---

## Configuration Files

### vite.config.ts
Configures the Vite build system:
- **React Plugin**: Enables React with SWC (faster than Babel)
- **Path Aliases**: Simplifies imports (e.g., `@/components/...`)
- **Build Output**: Targets `build/` directory
- **Dev Server**: Runs on port 3000, auto-opens browser

### package.json
Defines:
- **Dependencies**: All UI libraries and utilities
- **Scripts**:
  - `npm run dev`: Start development server
  - `npm run build`: Build production bundle

---

## Docker Setup

### Dockerfile (Multi-Stage Build)

The Dockerfile uses a **two-stage build** for optimal production deployment:

#### **Stage 1: Builder**
- **Base Image**: `node:20-alpine` (lightweight Node.js 20 on Alpine Linux)
- **Purpose**: Install dependencies and build the React application
- **Process**:
  1. Copy `package.json`
  2. Run `npm install` to install all dependencies
  3. Copy source code
  4. Run `npm run build` to create production build in `build/` directory

#### **Stage 2: Production Server**
- **Base Image**: `nginx:alpine` (lightweight Nginx web server)
- **Purpose**: Serve the static production build
- **Process**:
  1. Copy built assets from builder stage to Nginx HTML directory
  2. Expose port 80
  3. Start Nginx to serve the application

**Benefits of Multi-Stage Build:**
- **Small Image Size**: Final image only contains built assets + Nginx (no Node.js or build tools)
- **Security**: Reduces attack surface by excluding unnecessary dependencies
- **Fast Deployment**: Optimized for production serving

### .dockerignore

Excludes unnecessary files from the Docker build context:
- `node_modules/` (will be installed fresh in container)
- Build artifacts (`build/`, `dist/`)
- Environment files
- IDE and editor files
- Documentation files

**Benefits:**
- Faster builds (smaller context)
- Smaller images
- Prevents local artifacts from contaminating the build

---

## Running the UI

### Prerequisites
- **Docker**: Installed and running on your machine
- **Port 80**: Available (or modify Dockerfile to use a different port)

### Option 1: Local Development (Without Docker)

If you want to run the UI locally for development:

```bash
# Navigate to the UI directory
cd src/ui

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will open automatically at `http://localhost:3000`.

**Development Features:**
- Hot Module Replacement (HMR): Changes reflect instantly
- Fast Refresh: Preserves component state during edits
- TypeScript type checking in real-time

### Option 2: Docker Production Build

For production-ready containerized deployment:

#### Step 1: Build the Docker Image

```bash
# Navigate to the UI directory
cd src/ui

# Build the Docker image (tagged as 'cad-coder-ui')
docker build -t cad-coder-ui .
```

**Expected Output:**
- Stage 1: Dependencies installed, application built
- Stage 2: Nginx configured with built assets
- Final image size: ~50-70 MB (depending on build)

#### Step 2: Run the Docker Container

```bash
# Run the container, mapping port 80 to host port 8080
docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui
```

**Flags Explained:**
- `-d`: Run in detached mode (background)
- `-p 8080:80`: Map container port 80 to host port 8080
- `--name cad-coder-ui-container`: Assign a name to the container
- `cad-coder-ui`: The image to run

#### Step 3: Access the Application

Open your browser and navigate to:
```
http://localhost:8080
```

**Note:** If port 8080 is already in use, change it to another port (e.g., `-p 3000:80` for `http://localhost:3000`).

---

## Docker Management Commands

### View Running Containers
```bash
docker ps
```

### View Container Logs
```bash
docker logs cad-coder-ui-container
```

### Stop the Container
```bash
docker stop cad-coder-ui-container
```

### Start the Container Again
```bash
docker start cad-coder-ui-container
```

### Remove the Container
```bash
docker rm cad-coder-ui-container
```

### Remove the Image
```bash
docker rmi cad-coder-ui
```

### Rebuild After Code Changes
```bash
# Stop and remove the old container
docker stop cad-coder-ui-container
docker rm cad-coder-ui-container

# Rebuild the image
docker build -t cad-coder-ui .

# Run the new container
docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui
```

---

## Usage Instructions

### 1. **Create a New Chat Session**
- Click the **"New Chat"** button in the sidebar
- A new session will be created and activated

### 2. **Select an AI Model**
- Use the **Model Selector** dropdown at the top
- Choose between:
  - **Baseline-LLaVA**: Best for multimodal (text + image) tasks
  - **Qwen-2.5-xB**: Best for code generation and reasoning

### 3. **Send a Text Query**
- Type your message in the input box at the bottom
- Press **Enter** or click the **Send** button
- The AI will respond with a mock reply (no actual LLM integration yet)

### 4. **Upload an Image (Multimodal Query)**
- Click the **file upload icon** (📎) in the input area
- Select an image file (PNG, JPG, etc.)
- Type an accompanying message (optional)
- Send the query
- The AI will acknowledge the image and provide a multimodal response

### 5. **Switch Between Sessions**
- Click on any session in the sidebar to view its history
- Each session maintains its own conversation history

### 6. **Delete a Session**
- Hover over a session in the sidebar
- Click the **trash icon** to delete it
- The next available session will be automatically selected

---

## Current Limitations & Future Enhancements

### Current Limitations
- **Mock Responses Only**: AI responses are pre-defined mock strings, not real LLM outputs
- **No Backend Integration**: The UI is standalone and does not connect to the RAG pipeline or inference backend yet
- **Session Persistence**: Chat sessions are lost on page refresh (no database/storage)
- **Single User**: No multi-user support or authentication

### Planned Enhancements
- **Backend API Integration**: Connect to the RAG pipeline and LLM inference endpoints
- **Real AI Responses**: Replace mock responses with actual model outputs (Baseline-LLaVA, Qwen-2.5-xB, etc.)
- **Session Persistence**: Store chat history in a database (e.g., PostgreSQL, MongoDB)
- **User Authentication**: Add login/signup with session management
- **Streaming Responses**: Implement real-time streaming of AI responses (like ChatGPT)
- **CAD Code Visualization**: Display generated CAD code with syntax highlighting
- **Advanced RAG Controls**: Allow users to configure retrieval parameters (top-k, similarity threshold, etc.)
- **Model Performance Metrics**: Show response time, token count, and quality scores

---

## Troubleshooting

### Issue: Port 80 already in use
**Solution:** Use a different host port when running the container:
```bash
docker run -d -p 3000:80 --name cad-coder-ui-container cad-coder-ui
```

### Issue: Changes not reflected in Docker container
**Solution:** Rebuild the Docker image after making code changes:
```bash
docker build -t cad-coder-ui .
docker stop cad-coder-ui-container && docker rm cad-coder-ui-container
docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui
```

### Issue: Container exits immediately
**Solution:** Check container logs for errors:
```bash
docker logs cad-coder-ui-container
```

### Issue: Blank page or 404 error
**Solution:** Verify the build output directory matches Nginx configuration:
- Ensure `vite.config.ts` has `outDir: 'build'`
- Ensure Dockerfile copies from `/app/build` to `/usr/share/nginx/html`

---

## Development Workflow

### For Active Development
1. Use `npm run dev` for local development with HMR
2. Make changes to components in `src/components/`
3. Test in browser at `http://localhost:3000`
4. Commit changes to version control

### For Production Testing
1. Build Docker image: `docker build -t cad-coder-ui .`
2. Run container: `docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui`
3. Test at `http://localhost:8080`
4. Iterate as needed

### For Deployment
1. Push Docker image to a registry (e.g., Docker Hub, Google Container Registry)
2. Deploy to production environment (e.g., Google Cloud Run, Kubernetes)
3. Configure domain and SSL/TLS certificates

---

## References

- **Radix UI Documentation**: [https://www.radix-ui.com/](https://www.radix-ui.com/)
- **Vite Documentation**: [https://vitejs.dev/](https://vitejs.dev/)
- **React Documentation**: [https://react.dev/](https://react.dev/)
- **Docker Documentation**: [https://docs.docker.com/](https://docs.docker.com/)

---

## Contact & Support

For questions or issues related to the UI:
- Review the main project documentation in `/src/datapipeline/milestone2.md`
- Check the RAG pipeline integration docs in `/src/datapipeline/rag/milestone2.3_rag.md`
- Refer to the end-to-end pipeline docs in `/src/datapipeline/milestone2.2_endtoend.md`

---

**Last Updated:** October 28, 2025  
**Version:** 0.1.0  
**Status:** Development (Mock Interface - Backend Integration Pending)

