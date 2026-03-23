# Design Document: CifraPartit Music Transcription Platform

## Overview

CifraPartit é uma plataforma web de transcrição musical baseada em IA que converte áudio/vídeo em notação musical editável. A arquitetura segue um modelo cliente-servidor com processamento assíncrono de IA, editor web interativo e sistema de gerenciamento de usuários com modelo freemium.

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WebApp[Web Application]
        Editor[Score Editor]
        Recorder[Browser Recorder]
    end
    
    subgraph "API Gateway"
        REST[REST API]
        WS[WebSocket]
    end
    
    subgraph "Application Layer"
        Auth[Auth Service]
        User[User Service]
        Trans[Transcription Service]
        Export[Export Service]
    end
    
    subgraph "Processing Layer"
        Queue[Job Queue]
        AIEngine[AI Transcription Engine]
        OCR[OCR Scanner]
        KeyDet[Key Detector]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        FileStore[Object Storage]
        Cache[Redis Cache]
    end
    
    WebApp --> REST
    WebApp --> WS
    REST --> Auth
    REST --> User
    REST --> Trans
    REST --> Export
    Trans --> Queue
    Queue --> AIEngine
    Queue --> OCR
    Queue --> KeyDet
    Auth --> DB
    User --> DB
    Trans --> DB
    Trans --> FileStore
    Export --> FileStore
    AIEngine --> Cache
