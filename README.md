# 💰 Expense Tracker - Personal Finance Management System

A modern, full-stack expense tracking application that helps individuals manage their finances with beautiful visualizations, multi-currency support, and comprehensive analytics.

![Expense Tracker](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%2B%20React%20%2B%20MongoDB-orange)

## 🌟 Features

### 🔐 **Authentication & Security**
- **Google OAuth Integration** via Emergent Authentication
- Secure session management with HTTP-only cookies
- Multi-user support with data isolation
- Automatic session expiry and refresh

### 💳 **Transaction Management**
- **Complete CRUD Operations** - Create, Read, Update, Delete transactions
- **Smart Categorization** - 13 expense categories & 7 income categories
- **Date Range Filtering** - Filter transactions by date and category
- **Transaction Types** - Income and Expense tracking
- **Bulk Operations** - Mass import/export capabilities

### 🌍 **Multi-Currency Support**
- **20+ International Currencies** including USD, EUR, GBP, JPY, INR, and more
- **Real-time Currency Formatting** with proper symbols (€, £, ¥, ₹, etc.)
- **User Preferences** - Personal currency settings that persist
- **Automatic Conversion Display** - All amounts shown in selected currency

### 📊 **Advanced Analytics & Visualizations**
- **Interactive Dashboard** with real-time statistics
- **Chart.js Integration** - Beautiful pie charts, bar charts, and line graphs
- **Category Breakdown** - Visual spending analysis by category
- **Monthly Trends** - Track income vs expenses over time
- **Balance Tracking** - Real-time financial health monitoring

### 📄 **Export & Reporting**
- **CSV Export** - Download transaction data for Excel/Sheets
- **PDF Reports** - Professional reports with ReportLab integration
- **Summary Statistics** - Comprehensive financial summaries
- **Printable Format** - Clean, professional report layouts

### 🎨 **Modern UI/UX**
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Tailwind CSS** - Beautiful, modern interface
- **Dark Theme Support** - Easy on the eyes
- **Intuitive Navigation** - Clean, user-friendly design
- **Loading States** - Smooth user experience with proper feedback

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **MongoDB** - NoSQL database for flexible data storage
- **Pydantic** - Data validation and serialization
- **ReportLab** - PDF generation for reports
- **Motor** - Async MongoDB driver

### Frontend
- **React 18** - Modern UI library with hooks
- **Chart.js** - Interactive charts and visualizations
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **React Context** - State management for authentication

### Infrastructure
- **Docker** - Containerized deployment
- **Kubernetes** - Container orchestration
- **Supervisor** - Process management
- **CORS** - Cross-origin resource sharing

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Yarn package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/expense-tracker.git
cd expense-tracker
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure your MongoDB URL and other environment variables
```

3. **Frontend Setup**
```bash
cd frontend
yarn install
yarn start
```

4. **Environment Variables**

Backend `.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=expense_tracker
CORS_ORIGINS=http://localhost:3000
```

Frontend `.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

5. **Start the Application**
```bash
# Backend (Terminal 1)
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend (Terminal 2)
cd frontend
yarn start
```

Visit `http://localhost:3000` to access the application.

## 📋 API Documentation

### Authentication Endpoints
```http
GET  /api/auth/session-data     # Process OAuth session
POST /api/auth/logout           # Logout user
GET  /api/auth/me              # Get current user info
```

### Transaction Endpoints
```http
GET    /api/transactions        # Get user transactions
POST   /api/transactions        # Create new transaction
GET    /api/transactions/{id}   # Get specific transaction
PUT    /api/transactions/{id}   # Update transaction
DELETE /api/transactions/{id}   # Delete transaction
```

### Analytics Endpoints
```http
GET /api/dashboard/stats        # Dashboard statistics
GET /api/analytics/monthly      # Monthly analytics data
```

### Export Endpoints
```http
GET /api/export/csv            # Export as CSV
GET /api/export/pdf            # Export as PDF
```

### Utility Endpoints
```http
GET /api/categories            # Available categories
GET /api/currencies           # Supported currencies
PUT /api/user/settings        # Update user preferences
```

## 📱 Usage Examples

### Adding a Transaction
```javascript
const transaction = {
  type: "expense",
  amount: 50.00,
  category: "Food & Dining",
  description: "Lunch at restaurant",
  date: new Date().toISOString()
};

await axios.post('/api/transactions', transaction);
```

### Changing Currency
```javascript
const settings = { currency: "EUR" };
await axios.put('/api/user/settings', settings);
```

### Exporting Data
```javascript
// CSV Export
const csvData = await axios.get('/api/export/csv', { 
  responseType: 'blob' 
});

// PDF Export
const pdfData = await axios.get('/api/export/pdf', { 
  responseType: 'blob' 
});
```

## 🎯 Key Features in Detail

### 💱 Multi-Currency Support
The application supports 20+ international currencies:
- 🇺🇸 US Dollar ($)
- 🇪🇺 Euro (€)
- 🇬🇧 British Pound (£)
- 🇯🇵 Japanese Yen (¥)
- 🇮🇳 Indian Rupee (₹)
- 🇰🇷 South Korean Won (₩)
- 🇷🇺 Russian Ruble (₽)
- And many more...

### 📊 Analytics Dashboard
- **Real-time Statistics**: Total income, expenses, balance, transaction count
- **Visual Charts**: Category breakdown pie charts, monthly trend analysis
- **Smart Insights**: Spending pattern recognition
- **Responsive Design**: Works on all devices

### 🔒 Security Features
- **OAuth 2.0**: Secure Google authentication
- **Session Management**: Secure token-based sessions
- **Data Isolation**: User data is completely isolated
- **CORS Protection**: Proper cross-origin resource sharing

## 🚦 Project Status

- ✅ **Authentication System** - Complete
- ✅ **Transaction CRUD** - Complete
- ✅ **Analytics Dashboard** - Complete
- ✅ **Multi-Currency Support** - Complete
- ✅ **Export Functionality** - Complete
- ✅ **Responsive UI** - Complete
- ✅ **Data Visualization** - Complete

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Emergent Authentication** for seamless OAuth integration
- **Chart.js** for beautiful data visualizations
- **ReportLab** for PDF generation capabilities
- **Tailwind CSS** for modern UI components
- **FastAPI** for the excellent Python framework

## 📞 Support

If you encounter any issues or have questions:

1. ** MAIL ** : Aarizqureshi.20211081@gmail.com

## 🌟 Star History

If you find this project helpful, please consider giving it a star on GitHub!

---

<div align="center">
  <p><strong>Made with ❤️ for better financial management</strong></p>
  <p>
    <a href="#top">Back to Top</a>
  </p>
</div>
