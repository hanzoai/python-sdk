# Hanzo Unified Services Architecture

## Overview
This document outlines the architecture for unified Hanzo services including memory, authentication, and AI infrastructure.

## Components

### 1. Authentication & Identity Management (IAM) - `~/work/hanzo/iam`

#### Current State
- Located at `~/work/hanzo/iam`
- Based on Casdoor upstream at `~/work/cas/casdoor`
- Not yet fully completed

#### Requirements
- Complete integration with upstream Casdoor
- Deploy at hanzo.id for user authentication
- API key management system
- OAuth2/OpenID Connect support
- Role-based access control (RBAC)
- Multi-tenant support

#### Features
- User registration/login
- API key generation and management
- Service-specific permissions
- Audit logging
- Rate limiting per user/api-key

### 2. Memory Server - `~/work/hanzo/gateway`

#### Location
- Part of the gateway infrastructure at `~/work/hanzo/gateway`
- Would expose memory services via REST/gRPC APIs

#### Architecture
- Built on the modular plugin architecture we just implemented
- Support for multiple backends (SQLite, LanceDB, Redis, etc.)
- Authentication via IAM system
- Rate limiting and quotas
- Multi-tenant isolation

#### API Endpoints
```
POST /v1/memory/store
GET  /v1/memory/retrieve
POST /v1/memory/search
DELETE /v1/memory/{id}
GET  /v1/memory/capabilities
```

#### Authentication
- Require valid API key from IAM system
- Validate permissions for specific operations
- Support for service-to-service authentication

### 3. Inference Gateway - `~/work/hanzo/gateway`

#### Current State
- Already exists with embeddings server
- Provides inference services

#### Integration Points
- Share authentication infrastructure with IAM
- Unified API key system
- Consistent rate limiting and quotas

### 4. Hanzo Extension - `~/work/hanzo/extension`

#### Components
- Web extension
- VS Code extension

#### Services Accessed
- Memory server for unified memory
- Search service for indexing and retrieval
- Inference gateway for AI operations
- Rules engine for business logic

#### Authentication Flow
1. User authenticates via hanzo.id
2. Gets API key for specific services
3. Extension uses API keys to access backend services
4. All requests are authenticated and authorized

## Deployment Architecture

### Public Services
- hanzo.id - Authentication and user management
- gateway.hanzo.ai - Inference and memory services
- api.hanzo.ai - Unified API endpoints

### Internal Services
- IAM service (private)
- Memory server (private, exposed via gateway)
- Inference gateway (private, exposed via gateway)

## Security Model

### Authentication
- OAuth2/OpenID Connect via Casdoor
- API key authentication for service access
- JWT tokens for session management

### Authorization
- Role-based access control
- Service-specific permissions
- Resource-level access control

### Data Isolation
- Multi-tenant data separation
- Encrypted storage for sensitive data
- Secure data transmission

## Implementation Roadmap

### Phase 1: Complete IAM
1. Merge upstream Casdoor changes
2. Complete user authentication system
3. Implement API key management
4. Deploy at hanzo.id

### Phase 2: Memory Server
1. Extend gateway to include memory services
2. Implement authentication integration
3. Add rate limiting and quotas
4. Deploy memory server

### Phase 3: Extension Integration
1. Update extensions to use new APIs
2. Implement authentication flows
3. Add unified memory features
4. Deploy updated extensions

### Phase 4: Advanced Features
1. Multi-region deployment
2. Enhanced security features
3. Analytics and monitoring
4. Developer tools and SDKs

## Benefits

### For Users
- Single sign-on across all Hanzo services
- Consistent API experience
- Secure access to all features
- Centralized billing and quotas

### For Developers
- Standardized authentication
- Reusable components
- Scalable architecture
- Comprehensive tooling

### For Business
- Unified user management
- Consistent revenue model
- Reduced operational overhead
- Enhanced security posture

## Technical Considerations

### Scalability
- Horizontal scaling for all services
- Database sharding for large deployments
- CDN for static assets
- Load balancing

### Reliability
- Health checks and monitoring
- Automatic failover
- Backup and recovery
- Disaster recovery plans

### Performance
- Caching strategies
- Optimized database queries
- Efficient data serialization
- Connection pooling

This architecture provides a solid foundation for a unified Hanzo services platform that scales with demand while maintaining security and reliability.