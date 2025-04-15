# AI-Powered VM Creator Platform

A sophisticated cloud infrastructure management platform that leverages AI to automatically suggest and provision virtual machines based on user requirements. This project demonstrates expertise in cloud computing, AI integration, and full-stack web development.

## 📸 Application Screenshots

### AI-Powered VM Creation Interface
![VM Creation Interface](docs/vm-creation.png)
*Natural language input for VM requirements with AI-powered suggestions*

### Real-time Deployment Status
![Deployment Status](docs/deployment-status.png)
*Live monitoring of VM provisioning with detailed status updates*

### VM Management Dashboard
![Management Dashboard](docs/vm-management.png)
*Centralized dashboard for managing multiple VM instances*

### Instance Configuration Review
![Configuration Review](docs/config-review.png)
*Detailed configuration review before deployment*

## 🚀 Key Features

- **AI-Powered VM Configuration**
  - Natural language processing for VM requirements
  - Intelligent resource allocation suggestions
  - Automated configuration generation

- **Cloud Infrastructure Management**
  - Automated VM provisioning on GCP
  - Real-time deployment status monitoring
  - Multi-region support with load balancing
  - Terraform-based infrastructure as code

- **Modern Web Interface**
  - Responsive, mobile-first design
  - Real-time status updates
  - Intuitive user experience
  - Modern UI with animations and transitions

- **Security & Authentication**
  - Secure user authentication
  - Session management with Redis
  - Role-based access control
  - Secure key management for VM access

## 🛠️ Technology Stack

### Backend
- **Framework:** Flask (Python)
- **AI Integration:** OpenAI API
- **Infrastructure:** Terraform, Google Cloud Platform
- **Database:** PostgreSQL
- **Caching:** Redis
- **Task Queue:** Celery
- **Authentication:** Flask-Session

### Frontend
- **HTML5/CSS3** with modern features
- **JavaScript** for dynamic interactions
- **Font Awesome** for icons
- **Inter** font family for typography
- **CSS Grid/Flexbox** for layouts

### DevOps
- **Containerization:** Docker
- **CI/CD:** GitHub Actions
- **Monitoring:** GCP Cloud Monitoring
- **Logging:** Structured logging with rotation

## 🏗️ Architecture

```plaintext
Client <-> Nginx <-> Flask App <-> Celery Workers
                        |
                        ├── Redis (Sessions/Cache)
                        ├── PostgreSQL (Data Store)
                        ├── OpenAI API (VM Suggestions)
                        └── GCP (VM Provisioning)
```

## 💡 Technical Highlights

1. **AI Integration**
   - Natural language processing for understanding user requirements
   - Machine learning for optimal resource allocation
   - Continuous learning from user feedback

2. **Cloud Infrastructure**
   - Infrastructure as Code using Terraform
   - Automated VM provisioning and configuration
   - Multi-region deployment support
   - Auto-scaling capabilities

3. **Security Features**
   - Secure session management
   - HTTPS enforcement
   - Protected API endpoints
   - Secure credential storage

4. **Performance Optimization**
   - Redis caching for session data
   - Asynchronous task processing with Celery
   - Optimized database queries
   - Content delivery optimization

## 🚀 Getting Started

1. **Prerequisites**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/vm-creator.git
   cd vm-creator

   # Set up Python virtual environment
   python -m venv myenv
   source myenv/bin/activate  # or `myenv\Scripts\activate` on Windows
   ```

2. **Environment Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Configure environment variables
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Database Setup**
   ```bash
   # Initialize the database
   flask db upgrade
   ```

4. **Running the Application**
   ```bash
   # Start Redis
   redis-server

   # Start Celery worker
   celery -A app.celery worker --loglevel=info

   # Run the application
   flask run
   ```

## 🔧 Configuration

The application can be configured through environment variables:

- `FLASK_ENV`: Development/Production mode
- `OPENAI_API_KEY`: OpenAI API credentials
- `GCP_PROJECT_ID`: Google Cloud Project ID
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## 📈 Future Enhancements

- Kubernetes deployment support
- Machine learning for predictive scaling
- Extended cloud provider support (AWS, Azure)
- Advanced monitoring and analytics
- Container orchestration integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Your Name
- LinkedIn: [Your LinkedIn]()
- GitHub: [Your GitHub]()
- Portfolio: [Your Portfolio]()

---
*Note: Replace placeholder links and information with your actual details before publishing.* 