# Vending Machine Dashboard Documentation

## Overview
This documentation outlines the structure and usage of the Vending Machine Dashboard built with Vue 3, Vite, and Tailwind CSS.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/calixtaaa/Thesis.git
   cd Thesis
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Run the Development Server**:
   ```bash
   npm run dev
   ```

## Project Structure
- **src/**: Contains the main application code.
  - **components/**: Vue components used in the application.
  - **views/**: Different views for routing.
  - **assets/**: Static files like images and styles.

- **public/**: Static assets that are served directly.

## Usage
- Navigate to the dashboard at `http://localhost:3000`.
- You can interact with the vending machine features, manage inventory, and view analytics.

## Styling
The project uses Tailwind CSS for styling. Here are some key classes:
- **Flex Utilities**: Used for layout adjustments.
- **Margin and Padding**: Use classes like `m-4` and `p-2` for spacing.

## Building for Production
To build the application for production, run:
```bash
npm run build
```
This will output the files to the `dist/` directory.

## Deployment
You can deploy the contents of the `dist/` directory to your web server.

## Conclusion
This describes the basic setup and structure of the Vending Machine Dashboard. For detailed API documentation, refer to the separate API docs in the repository.