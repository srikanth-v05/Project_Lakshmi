# Smart Waste Management System

## Overview
The **Smart Waste Management System** is an AI and IoT-powered platform that optimizes waste collection processes in smart cities. Leveraging real-time sensor data, predictive analytics, and Intel’s oneAPI, this system reduces costs, lowers environmental impact, and improves operational efficiency.

## Key Features
- **Real-time Garbage Monitoring** using **AHP32 Ultrasonic Sensors**.
- **Predictive Garbage Accumulation** with an ensemble model (Random Forest, XGBoost, Gradient Boosting) optimized via **Intel’s Parallel Processing Toolkit (Sklearnex)** and **DPCTL**.
- **Dynamic Vehicle** Allocation and routing based on predicted waste levels.
- **User Features:** Photo-based complaints, garbage classification with **OPENVINO**, and **Lakshmi** the **Gemini (Generative AI)**-powered chatbot.
- **Event-based Waste Management** and scheduling.
- **Real-time Dashboard** for fill levels, predictive waste, vehicle routing, events, and user queries.

## Table of Contents
- System Architecture
- Technology Stack
- Prerequisites
- Installation
- Usage
- Project Structure
- API Endpoints
- Contributing
- License
- Contact

  ## System Architecture
  
  ![Flow chart of the Smart Waste Management System](/flowchart.jpg)

## Technology Stack
-**Intel oneAPI:** For performance optimizations and parallel processing.
-**AHP32 Ultrasonic Sensors:** For real-time fill level monitoring.
-**IoT:** To trigger alerts for bins exceeding 90% fill capacity.
-**Machine Learning Models:**
  -**Random Forest**, **XGBoost**, **Gradient Boosting**.
  -Optimized with **Intel Sklearnex** and **DPCTL**.
-**OPENVINO:** For garbage classification in photo-based complaints.
-**Gemini (Generative AI):** Powers Lakshmi, the user interaction chatbot.

## Prerequisites
-**Python 3.8+**
-**Intel oneAPI Base Toolkit** (with **Sklearnex**, **DPCTL**, **Threading Building Blocks**)
-**OPENVINO** (for image processing)
-**IoT Devices:** AHP32 Ultrasonic Sensors for real-time data collection
-**Git**

## Installation
### Step 1: Clone the Repository
```bash
git clone https://github.com/username/smart-waste-management.git
cd smart-waste-management
```
### Step 2: Install Required Libraries
It is recommended to set up a virtual environment:
```
python -m venv env
source env/bin/activate    # Linux/MacOS
env\Scripts\activate       # Windows
```
Install the dependencies:
```
pip install -r requirements.txt
```
### Step 3: Setup Intel oneAPI
Ensure you have Intel oneAPI installed and configured on your system. Instructions can be found [here](https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html).

For **Sklearnex** and **DPCTL**:
```
pip install scikit-learn-intelex dpctl
```
### Step 4: Setup IoT Sensors (AHP32)
Configure the AHP32 ultrasonic sensors for real-time data collection:

-Ensure proper connection and setup of sensors with the bins.
-Set up an MQTT broker or other IoT communication protocols to send data to the system.

## Usage
### Running the System
1. **Start the Sensor Data Collection:** The system will collect real-time data from the AHP32 Ultrasonic Sensors and log fill levels.
```
python sensor_data_collection.py
```
2. **Run Predictive Model:** The ensemble machine learning model will predict future waste levels and trigger vehicle routing based on predictions.
```
python waste_prediction.py
```
3. **Dashboard Access:** Open the dashboard in your browser to monitor real-time fill levels, vehicle routing, event schedules, and user queries.
```
python dashboard.py
```
4. **User Interaction:** Users can interact with the Lakshmi chatbot for event registration, complaint reporting, and garbage classification.
```
python chatbot.py
```
## Project Structure
```
smart-waste-management/
├── sensors/                      # IoT Sensor Data Collection
│   └── ahp32_sensor.py
├── models/                       # Machine Learning Models for Prediction
│   └── waste_prediction_model.py
├── classifier/                   # Garbage Classification Module (OPENVINO)
│   └── garbage_classifier.py
├── chatbot/                      # Lakshmi Chatbot (Gemini AI)
│   └── chatbot.py
├── dashboard/                    # Real-time Dashboard Code
│   └── dashboard.py
├── requirements.txt              # Python dependencies
└── README.md                     # Project Documentation
```

