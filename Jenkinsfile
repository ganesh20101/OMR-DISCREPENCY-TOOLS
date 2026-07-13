pipeline {
    agent any

    environment {
        // ==========================
        // USER CONFIGURATION
        // ==========================
        BASE_DIR = 'C:\\jssc'

        // Template JSON
        TEMPLATE_PATH = 'C:/New_folder/all_images/template/jssc.gs'

        // Template image used for alignment
        TEMPLATE_IMAGE = 'C:/New_folder/all_images/template/2024.07.18 12.29.42F.jpg'

        // Python scripts
        ALIGN_SCRIPT = 'C:/scripts/align.py'
        SCAN_SCRIPT  = 'C:/scripts/scan.py'

        // Alignment options
        ALIGN_IMAGES = 'true'
        FORCE_ALIGNMENT = 'false'
        ALIGNMENT_DONE_FILE = 'alignment_done.txt'

        // Scan marker
        SCAN_DONE_FILE = 'scan_done.txt'
    }

    stages {

        stage('Verify Python') {
            steps {
                bat '''
                python --version
                if errorlevel 1 (
                    echo Python not installed or PATH not configured.
                    exit /b 1
                )
                '''
            }
        }

        stage('Verify Inputs') {
            steps {
                powershell '''
                    if (-not (Test-Path "$env:BASE_DIR")) {
                        Write-Error "ERROR: BASE_DIR not found: $env:BASE_DIR"
                        exit 1
                    }
                    if (-not (Test-Path "$env:TEMPLATE_PATH")) {
                        Write-Error "ERROR: TEMPLATE_PATH not found: $env:TEMPLATE_PATH"
                        exit 1
                    }
                    if (-not (Test-Path "$env:TEMPLATE_IMAGE")) {
                        Write-Error "ERROR: TEMPLATE_IMAGE not found: $env:TEMPLATE_IMAGE"
                        exit 1
                    }
                    if (-not (Test-Path "$env:ALIGN_SCRIPT")) {
                        Write-Error "ERROR: ALIGN_SCRIPT not found: $env:ALIGN_SCRIPT"
                        exit 1
                    }
                    if (-not (Test-Path "$env:SCAN_SCRIPT")) {
                        Write-Error "ERROR: SCAN_SCRIPT not found: $env:SCAN_SCRIPT"
                        exit 1
                    }
                    Write-Host "Input verification successful."
                '''
            }
        }

        stage('Process Subfolders') {
            steps {
                script {
                    // Find subfolders that contain F.jpg files
                    def subfolders = powershell(
                        returnStdout: true,
                        script: """
                        \$dirs = Get-ChildItem -Path \$env:BASE_DIR | Where-Object { \$_.PSIsContainer }
                        \$result = @()
                        foreach (\$d in \$dirs) {
                            \$full = \$d.FullName
                            if ((Get-ChildItem -Path \$full -Recurse -Filter '*F.jpg' -File).Count -gt 0) {
                                \$result += \$full
                            }
                        }
                        \$result -join "`n"
                        """
                    ).trim().split('\\r?\\n').findAll { it }

                    if (!subfolders) {
                        error "No subfolders with F.jpg files found under ${env.BASE_DIR}"
                    }

                    echo "Found ${subfolders.size()} subfolders to process: ${subfolders}"

                    for (subfolder in subfolders) {
                        def folderName = subfolder.replaceAll(/^.*[\\\\\\/]/, '')
                        echo "========================================"
                        echo "Processing subfolder: ${folderName}"
                        echo "Path: ${subfolder}"
                        echo "========================================"

                        // --- Alignment ---
                        def alignMarker = "${subfolder}\\${env.ALIGNMENT_DONE_FILE}"
                        def alignmentNeeded = true
                        if (fileExists(alignMarker)) {
                            echo "Alignment already completed for ${folderName}."
                            alignmentNeeded = false
                        } else {
                            echo "Alignment required for ${folderName}."
                            alignmentNeeded = true
                        }

                        if (env.ALIGN_IMAGES == 'true' && (env.FORCE_ALIGNMENT == 'true' || alignmentNeeded)) {
                            bat """
                            python "%ALIGN_SCRIPT%" "%TEMPLATE_IMAGE%" "${subfolder}"
                            """
                            writeFile(file: alignMarker, text: 'Alignment complete.')
                            echo "Alignment completed for ${folderName}."
                        } else {
                            echo "Skipping alignment for ${folderName}."
                        }

                        // --- Scan ---
                        def scanMarker = "${subfolder}\\${env.SCAN_DONE_FILE}"
                        def csvFile = "${subfolder}\\${folderName}.csv"

                        if (fileExists(scanMarker)) {
                            echo "Scan already completed for ${folderName}. Skipping scan."
                            // If CSV exists, we'll copy it later (optional)
                        } else {
                            echo "Scanning ${folderName}..."
                            bat """
                            python "%SCAN_SCRIPT%" "%TEMPLATE_PATH%" "${subfolder}" "${csvFile}"
                            """
                            writeFile(file: scanMarker, text: 'Scan complete.')
                            echo "Scan completed for ${folderName}. CSV saved to ${csvFile}"
                        }

                        // Copy CSV to workspace (whether just created or already exists)
                        if (fileExists(csvFile)) {
                            bat "copy \"${csvFile}\" ."
                            echo "Copied ${folderName}.csv to workspace."
                        } else {
                            echo "Warning: CSV file ${csvFile} not found. No scan data for ${folderName}."
                        }
                    }
                }
            }
        }

        stage('Archive All CSVs') {
            steps {
                script {
                    // Archive all CSV files in the workspace (they were copied from subfolders)
                    archiveArtifacts artifacts: '*.csv', allowEmptyArchive: false
                    echo "Archived all CSV files."
                }
            }
        }
    }

    post {
        success {
            echo "====================================="
            echo "All subfolders processed successfully."
            echo "====================================="
        }
        failure {
            echo "====================================="
            echo "Pipeline Failed. Check Jenkins Console Output."
            echo "====================================="
        }
        always {
            echo "Pipeline Finished."
        }
    }
}
