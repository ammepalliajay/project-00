# Distributed Media Processing Microservice

An asynchronous event-driven media processing microservice using **FastAPI**, **Celery**, **RabbitMQ**, **Redis**, **Pillow**, and **FFmpeg** for scalable image and video processing jobs.

## Overview

This project provides a scalable, distributed media processing system that handles asynchronous image and video transformation tasks. It leverages a microservices architecture with task queuing, caching, and persistent storage.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **Task Queue**: Celery with RabbitMQ
- **Caching & Storage**: Redis
- **Media Processing**: FFmpeg, Pillow
- **Styling**: Tailwind CSS

## Project Structure

```
project-00/
├── media-processing-service/   # Python FastAPI backend
├── src/                        # React TypeScript frontend
├── storage/                    # Media storage directory
├── test_media/                 # Test media files
├── index.html                  # Main HTML entry point
├── package.json                # Node.js dependencies
├── tsconfig.json               # TypeScript configuration
├── vite.config.ts              # Vite configuration
├── .env.example                # Environment variables template
└── metadata.json               # Project metadata
```

## Getting Started

### Prerequisites

- Node.js (v16+)
- Python (v3.8+)
- RabbitMQ
- Redis
- FFmpeg

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ammepalliajay/project-00.git
   cd project-00
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Install frontend dependencies**
   ```bash
   npm install
   ```

4. **Set up Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

5. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

**Frontend (React with Vite)**
```bash
npm run dev
```
Runs on `http://localhost:3000`

**Backend (FastAPI)**
```bash
cd media-processing-service
uvicorn main:app --reload
```

**Build for Production**
```bash
npm run build
```

**Type Checking**
```bash
npm run lint
```

## Features

- **Asynchronous Processing**: Handle media processing jobs without blocking requests
- **Scalable Architecture**: Distribute processing tasks across multiple workers
- **Image Processing**: Transform images using Pillow
- **Video Processing**: Handle video conversions with FFmpeg
- **Task Queuing**: Manage job requests with Celery
- **Caching**: Redis-based caching for improved performance
- **RESTful API**: FastAPI-based backend with interactive documentation

## API Documentation

Once the backend is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Environment Configuration

See `.env.example` for required environment variables:
- Database connection strings
- RabbitMQ/Redis credentials
- API keys and configurations

## Development

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run clean` | Clean build artifacts |
| `npm run lint` | Run TypeScript type checking |

## Project Capabilities

- Server-side Gemini API integration
- Media upload and processing workflows
- Job status tracking
- Error handling and retry logic

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source. See the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an [issue](https://github.com/ammepalliajay/project-00/issues) on GitHub.

---

Built with ❤️ by ammepalliajay
