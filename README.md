[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Ic9iTi2K)

# Organization Management System

A web application for managing organization members, events, and registrations.

## Project Structure

```
final-project-htpham50/
├── app.js                 # Main Express application with all routes
├── public/                # Static assets
│   └── css/
│       └── style.css     # Application styles
├── partials/              # EJS includes
│   └── nav.ejs            # Navigation partial
├── package.json           # Dependencies
└── README.md              # This file
```

## Features

- **Member Management**: Add, edit, and delete organization members with different membership levels (Bronze, Silver, Gold)
- **Event Management**: Create and manage exclusive events with capacity limits and level-based access
- **Registration System**: Register members for events with automatic validation of level requirements and capacity
- **Dashboard**: Overview of total members, events, and registrations

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the Flask API server (from Sprint 1) on port 5000

3. Start the Express UI server:
   ```bash
   npm start
   ```

4. Open http://localhost:3000 in your browser

## Architecture

The application uses Express.js with EJS templating. All routes are defined inline in `app.js` for simplicity. API calls to the Flask backend are handled through a centralized helper function with proper error handling.
