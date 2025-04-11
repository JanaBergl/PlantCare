# 🪴 PlantCare

**PlantCare** is a Django-based web application designed to help users manage their houseplants by organizing care tasks like watering, fertilizing, and repotting. Users can add plants, sort them into groups, assign tasks with specific frequencies, and monitor upcoming or overdue activities.
> *The project is currently under active development.*

## Features

- **Plant management**: Add and manage plants with details such as name, group, date of purchase, and more.
- **Task scheduling**: Create custom tasks (e.g., watering, fertilizing) with specific frequencies for each plant.
- **Warnings overview**: Get an overview of due or overdue tasks for better plant care planning.
- **Task logging**: Mark tasks as completed and keep a history of actions taken.
- **Simple interface**: User-friendly interface for easy navigation and management.

## Installation

1. **Clone the repository**:

   ```
   git clone https://github.com/JanaBergl/PlantCare.git
   ```

2. **Create a virtual environment**:

   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   - On Windows:

     ```
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```
     source venv/bin/activate
     ```

4. **Install dependencies**:

   ```
   pip install -r requirements.txt
   ```

5. **Apply migrations**:

   ```
   python manage.py migrate
   ```

6. **Run the development server**:

   ```
   python manage.py runserver
   ```

7. **Access the application**:

   Open your browser and navigate to `http://127.0.0.1:8000/`.

## Technologies used

- **Backend**: Django  
- **Frontend**: HTML, CSS  
- **Database**: SQLite (default)

## Future enhancements

- **User authentication**: Allow multiple users with personalized plant collections.
- **Notifications**: Implement reminders for upcoming tasks.
- **Responsive design**: Improve layout for mobile devices.
- and more ...

## Author

Developed by [Jana Bergl](https://github.com/JanaBergl).
