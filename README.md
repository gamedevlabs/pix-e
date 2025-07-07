# Pix-e Monorepo Project

This project is a monorepo containing a Django backend and a Nuxt.js frontend, designed to provide a platform for game developers. This README details the project structure, setup instructions, and the implementation of a new "Sentiment Analysis" feature.

## Project Structure

*   **`backend/`**: A Django project serving as the API for the application. It handles data processing, database interactions, and exposes RESTful endpoints.
*   **`frontend/`**: A Nuxt.js (Vue.js) project that provides the user interface. It consumes data from the Django backend API.

## Setup and Installation

To get the project up and running, follow these steps:

1.  **Install `pyenv` (if not already installed):**
    `pyenv` is used to manage Python versions.
    ```bash
    brew install pyenv
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc # Or your shell's rc file
    exec "$SHELL" # Restart your shell
    ```

2.  **Install Python 3.10.0 via `pyenv`:**
    ```bash
    pyenv install 3.10.0
    ```

3.  **Set local Python version for the project:**
    Navigate to the root of the `pix-e` directory and set the local Python version. This creates a `.python-version` file.
    ```bash
    cd /Users/balkis/pix-e/
    pyenv local 3.10.0
    ```

4.  **Install Project Dependencies:**
    The `install.js` script automates the setup of both backend (Python virtual environment and pip packages) and frontend (npm packages) dependencies.
    *   **Note:** The `install.js` script was modified to use `~/.pyenv/shims/python` to ensure the correct Python version is used for the virtual environment creation.
    ```bash
    node install.js
    ```

5.  **Apply Django Migrations (Backend):**
    After installing backend dependencies, apply any pending database migrations.
    ```bash
    cd backend/
    source ./.venv/bin/activate
    python3 manage.py migrate
    cd ..
    ```

## Implemented Features: Sentiment Analysis Page

We have implemented a new "Sentiment Analysis" feature, accessible via a dedicated frontend page, which consumes data from a new backend API endpoint.

### Backend Implementation

A new Django app named `sentiments` was created to handle the sentiment data.

*   **`backend/sentiments/views.py`**:
    *   A `SentimentData` API view was created to read the `df_with_sentiments_explicit.csv` file.
    *   **Crucially**, the view was updated to handle `NaN` (Not a Number) values in the CSV by converting them to `None` (which translates to `null` in JSON) using `df.where(pd.notna(df), None).to_dict(orient='records')`. This prevents `ValueError: Out of range float values are not JSON compliant` errors during JSON serialization.
*   **`backend/sentiments/urls.py`**: Defines the `/api/sentiments/` endpoint for the `SentimentData` view.
*   **`backend/api/settings.py`**: The `sentiments` app was added to `INSTALLED_APPS`.
    *   `CORS_ALLOWED_ORIGINS` was updated to include `http://localhost:3002` to resolve Cross-Origin Resource Sharing (CORS) issues, allowing the frontend to fetch data from the backend.
*   **`backend/api/urls.py`**: The `sentiments.urls` were included in the main project URLs.
*   **`backend/requirements.txt`**: `pandas` was added to this file to enable CSV reading and processing.
*   **`df_with_sentiments_explicit.csv`**: This data file is expected to be in the root directory of the project (`/Users/balkis/pix-e/`).

### Frontend Implementation

A new Nuxt.js page and associated components were created to display and interact with the sentiment data.

*   **`frontend/pages/sentiments.vue`**:
    *   This is the main page component, accessible at `http://localhost:3002/sentiments`.
    *   It uses the `useSentiments` composable to fetch data.
    *   It integrates `SentimentFilters`, `SentimentTable`, `SentimentDistributionChart`, and `DominantAspectChart` components.
    *   The `filteredSentiments` computed property handles the filtering logic, ensuring that `filters.value.genre` and `filters.value.game` are treated as arrays for multi-selection. It also provides a default empty array (`[]`) if `sentiments.value` is not yet loaded, preventing "Cannot read properties of undefined (reading 'length')" errors during server-side rendering.
*   **`frontend/composables/useSentiments.ts`**:
    *   A Vue composable responsible for fetching the sentiment data from the `/api/sentiments/` endpoint.
*   **`frontend/components/SentimentFilters.vue`**:
    *   Provides dropdown filters for "Genre," "Sentiment," and "Game Name."
    *   **Enhanced Multi-Select:** The "Genre" and "Game Name" filters now use the `MultiSelectFilter` component, allowing multiple selections with a "tick inside" UI.
    *   The component emits a `filter-change` event with the selected filter values.
    *   Internal `selectedGenre` and `selectedGame` refs are now initialized and reset as arrays to maintain type consistency.
*   **`frontend/components/MultiSelectFilter.vue`**:
    *   A reusable Vue component that provides a multi-select dropdown with checkboxes.
    *   It takes `options` and `modelValue` (an array) as props.
    *   The dropdown options are displayed vertically.
*   **`frontend/components/SentimentTable.vue`**:
    *   Displays the filtered sentiment data in a tabular format.
    *   **Sorting:** Table headers are clickable to sort data by column (ascending/descending).
    *   **Pagination:** Includes controls to navigate through pages of data, with a default of 10 items per page.
*   **`frontend/components/SentimentDistributionChart.vue`**:
    *   Displays a donut chart showing the distribution of positive, negative, and neutral sentiments using `vue-chartjs`.
*   **`frontend/components/DominantAspectChart.vue`**:
    *   Displays a bar chart showing the top 10 most frequently mentioned "dominant aspects" using `vue-chartjs`.
*   **`frontend/assets/css/main.css`**:
    *   Modified to introduce a darker, "game-like" color scheme with vibrant accent colors, enhancing the overall UI aesthetics.

## How to Run the Project

1.  **Start the Backend Server:**
    Open a terminal, navigate to the `backend/` directory, activate the virtual environment, and start the Django development server.
    ```bash
    cd /Users/balkis/pix-e/backend/
    source ./.venv/bin/activate
    python3 manage.py runserver
    ```
    *Leave this terminal running.*

2.  **Start the Frontend Development Server:**
    Open a **new** terminal, navigate to the `frontend/` directory, and start the Nuxt.js development server.
    ```bash
    cd /Users/balkis/pix-e/frontend/
    npm run dev
    ```
    *Note the port number in the output (e.g., `http://localhost:3002/`).*

3.  **Access the Application:**
    Open your web browser and navigate to the frontend URL. To see the sentiment analysis page, go to:
    `http://localhost:3002/sentiments` (replace `3002` with the actual port if different).

## Troubleshooting Notes

*   **"Failed to fetch" / CORS Issues**: Ensure both backend and frontend servers are running. Check `backend/api/settings.py` for correct `CORS_ALLOWED_ORIGINS` (e.g., `http://localhost:3002`).
*   **"Cannot read properties of undefined (reading 'length')"**: This was resolved by ensuring `filters` and `selectedGenre`/`selectedGame` are consistently initialized and handled as arrays in `sentiments.vue` and `SentimentFilters.vue`.
*   **"Broken pipe"**: This is often a symptom of the client closing the connection prematurely after receiving data, not necessarily a server error preventing data transfer.
*   **Django Migrations**: If you see warnings about unapplied migrations, run `python3 manage.py migrate` in the `backend/` directory.