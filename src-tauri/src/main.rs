#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::collections::HashMap;
use std::process::Child;
use std::sync::Mutex;
use tauri::api::process::{Command, CommandEvent};
use tauri::AppHandle;

// State to hold the backend process
struct BackendProcess(Mutex<Option<Child>>);

#[tauri::command]
fn get_app_data_dir(app: AppHandle) -> String {
    app.path_resolver()
        .app_data_dir()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| String::from(""))
}

#[tauri::command]
async fn check_ollama_status() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();

    match client
        .get("http://localhost:11434/api/tags")
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
                match response.json::<serde_json::Value>().await {
                    Ok(data) => {
                        let models: Vec<String> = data
                            .get("models")
                            .and_then(|m| m.as_array())
                            .map(|arr| {
                                arr.iter()
                                    .filter_map(|m| m.get("name").and_then(|n| n.as_str()))
                                    .map(String::from)
                                    .collect()
                            })
                            .unwrap_or_default();

                        Ok(serde_json::json!({
                            "status": "running",
                            "models": models
                        }))
                    }
                    Err(_) => Ok(serde_json::json!({
                        "status": "running",
                        "models": []
                    }))
                }
            } else {
                Ok(serde_json::json!({
                    "status": "not_running",
                    "models": []
                }))
            }
        }
        Err(_) => Ok(serde_json::json!({
            "status": "not_running",
            "models": [],
            "help": "Please install and start Ollama from https://ollama.ai"
        }))
    }
}

#[tauri::command]
async fn check_backend_health() -> Result<bool, String> {
    let client = reqwest::Client::new();

    match client
        .get("http://localhost:8000/health")
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
    {
        Ok(response) => Ok(response.status().is_success()),
        Err(_) => Ok(false)
    }
}

fn start_backend_sidecar(app: &AppHandle) -> Result<(), String> {
    let app_data_dir = app
        .path_resolver()
        .app_data_dir()
        .ok_or("Failed to get app data directory")?;

    // Create data directory if it doesn't exist
    std::fs::create_dir_all(&app_data_dir).map_err(|e| e.to_string())?;

    let sqlite_path = app_data_dir.join("data").join("decisiongpt.db");

    // Ensure the data subdirectory exists
    if let Some(parent) = sqlite_path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    println!("Starting backend sidecar...");
    println!("SQLite path: {:?}", sqlite_path);

    // Spawn the backend sidecar process
    let mut envs = HashMap::new();
    envs.insert("DATABASE_TYPE".to_string(), "sqlite".to_string());
    envs.insert("SQLITE_PATH".to_string(), sqlite_path.to_str().unwrap_or("").to_string());
    envs.insert("LLM_PROVIDER".to_string(), "ollama".to_string());
    envs.insert("DESKTOP_MODE".to_string(), "true".to_string());
    envs.insert("CORS_ORIGINS".to_string(), "http://localhost:3000,tauri://localhost".to_string());

    let (mut rx, _child) = Command::new_sidecar("decisiongpt-backend")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?
        .envs(envs)
        .spawn()
        .map_err(|e| format!("Failed to spawn backend: {}", e))?;

    // Monitor backend output in a separate task
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => println!("[backend] {}", line),
                CommandEvent::Stderr(line) => eprintln!("[backend error] {}", line),
                CommandEvent::Error(err) => eprintln!("[backend error] {}", err),
                CommandEvent::Terminated(payload) => {
                    println!("[backend] Process terminated: {:?}", payload);
                    break;
                }
                _ => {}
            }
        }
    });

    println!("Backend sidecar started");
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle();

            // Start backend sidecar on app startup
            if let Err(e) = start_backend_sidecar(&handle) {
                eprintln!("Failed to start backend: {}", e);
                // Don't fail the app, user can start backend manually
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_app_data_dir,
            check_ollama_status,
            check_backend_health,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
