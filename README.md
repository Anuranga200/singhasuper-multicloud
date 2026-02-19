# Singha Super Loyalty System

A modern, feature-rich web application built with React, TypeScript, and Vite. This project provides a customer loyalty management system with admin dashboard capabilities.

## 🚀 Features

- **Customer Registration**: Easy onboarding process for new customers with validation
- **Admin Dashboard**: Comprehensive admin panel for managing customers and loyalty programs
- **JWT Authentication**: Secure token-based authentication with automatic token refresh
- **Responsive Design**: Mobile-first design using Tailwind CSS and Shadcn/ui components
- **Modern UI Components**: Built-in library of accessible, customizable UI components
- **AWS Integration**: Lambda and API Gateway backend integration
- **Real-time Updates**: React Query for efficient data fetching and caching

## 📋 Table of Contents

- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Available Scripts](#available-scripts)
- [Environment Variables](#environment-variables)
- [API Integration](#api-integration)
- [Authentication](#authentication)
- [Development](#development)
- [Building](#building)
- [Testing](#testing)
- [Contributing](#contributing)

## 🛠️ Tech Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Component Library**: Shadcn/ui with Radix UI primitives
- **Routing**: React Router v6
- **State Management**: React Query (@tanstack/react-query)
- **Form Handling**: React Hook Form
- **Icons**: Lucide React
- **Testing**: Vitest
- **Linting**: ESLint
- **Package Manager**: Bun

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Bun or npm

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Anuranga200/singha-super-connect.git
   cd singha-super-connect

##Project Structure

singha-super-connect/
├── src/
│   ├── components/          # Reusable React components
│   │   ├── ui/             # Shadcn/ui component library
│   │   ├── Header.tsx      # Header component
│   │   ├── Footer.tsx      # Footer component
│   │   ├── Layout.tsx      # Main layout wrapper
│   │   └── ...
│   ├── pages/              # Page components
│   │   ├── [Home.tsx](http://_vscodecontentref_/0)        # Homepage
│   │   ├── Register.tsx    # Customer registration
│   │   ├── AdminLogin.tsx  # Admin login
│   │   ├── AdminDashboard.tsx
│   │   ├── Privacy.tsx
│   │   ├── Terms.tsx
│   │   └── NotFound.tsx
│   ├── services/           # API services
│   │   └── [api.ts](http://_vscodecontentref_/1)         # API client with JWT integration
│   ├── hooks/             # Custom React hooks
│   │   ├── use-mobile.tsx
│   │   └── use-toast.ts
│   ├── lib/               # Utility libraries
│   │   ├── jwt.ts         # JWT utilities
│   │   └── utils.ts
│   ├── test/              # Test files
│   ├── [App.tsx](http://_vscodecontentref_/2)            # Main App component
│   └── main.tsx           # Application entry point
├── public/                # Static assets
├── [package.json](http://_vscodecontentref_/3)
├── [vite.config.ts](http://_vscodecontentref_/4)
├── [tsconfig.json](http://_vscodecontentref_/5)
├── [tailwind.config.ts](http://_vscodecontentref_/6)
└── [README.md](http://_vscodecontentref_/7)

##Environment Variables
# API Configuration
VITE_API_BASE_URL=http://localhost:3000/api

##Authentication

The application uses JWT (JSON Web Token) for authentication:

Access Token: Valid for 1 hour
Refresh Token: Valid for 7 days
Tokens are stored in localStorage
Automatic token refresh 5 minutes before expiration
Protected endpoints require Authorization header
Authentication Flow
Admin logs in via /admin endpoint
Server returns accessToken and refreshToken
Tokens are stored in localStorage
All subsequent API requests include the access token
When token expires, it's automatically refreshed
Logout clears all stored tokens

##API Integration
The application communicates with an AWS Lambda + API Gateway backend:

Available Endpoints
- **POST /admin/login - Admin login (returns JWT tokens)
- **POST /admin/refresh - Refresh expired access token
- **POST /customers/register - Register new customer
- **GET /customers - Fetch all customers (requires JWT)
- **DELETE /customers/{id} - Soft delete customer (requires JWT)

##Development

Project Setup

- **Install dependencies: bun install
- **Start dev server: bun run dev
- **Open http://localhost:8080 in your browser

Code Style
This project follows modern React and TypeScript best practices:

- **Functional components with hooks
- **TypeScript for type safety
- **ESLint for code quality
- **Responsive design with Tailwind CSS
- **Adding New Components
- **Use the Shadcn/ui components already included or create custom components in the components directory.



