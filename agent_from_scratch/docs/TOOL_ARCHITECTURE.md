# Project Tools Overview

This diagram represents the specific inputs, processing logic, and outputs for each tool built into the system.

```mermaid
graph LR
    subgraph Tools [/backend/tools/]
        T1[calculate]
        T2[get_weather]
        T3[process_file]
        T4[list_files]
    end

    subgraph Inputs [Pydantic Schemas]
        I1[CalculateInput: expression]
        I2[WeatherInput: location]
        I3[ProcessFileInput: filename]
        I4[ListFilesInput: empty]
    end

    subgraph Outputs [Results]
        O1[Math Result]
        O2[Weather Data]
        O3[Markdown Content]
        O4[File Metadata/Timestamps]
    end

    I1 --> T1 --> O1
    I2 --> T2 --> O2
    I3 --> T3 --> O3
    I4 --> T4 --> O4
```

## Tool Descriptions

| Tool | Purpose | Input | Output |
| :--- | :--- | :--- | :--- |
| **calculate** | Basic math operations | Math expression (string) | Calculated result |
| **get_weather** | Real-time weather data | City/Location name | Temp, wind speed, etc. |
| **process_file** | Doc-to-Markdown conversion | Filename from uploads | Full Markdown content |
| **list_files** | File system inspection | None | Metadata & Timestamps |
