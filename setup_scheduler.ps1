# Setup Windows Task Scheduler for Wake Detection
# Run this script as Administrator: powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1

$TaskName = "ProductivityIntelligence-WakeDetector"
$TaskDescription = "Checks for wake time and generates daily productivity report"
$BatchFile = "D:\Projects\Amazfit Watch Project\run_wake_detector.bat"

# Remove existing task if exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create trigger: Run every 30 minutes from 8 AM to 2 PM
$Triggers = @()

# Create triggers for 8:00, 8:30, 9:00, ..., 14:00 (every 30 mins)
$StartHour = 8
$EndHour = 14

for ($hour = $StartHour; $hour -le $EndHour; $hour++) {
    foreach ($minute in @(0, 30)) {
        if ($hour -eq $EndHour -and $minute -eq 30) { continue }  # Skip 14:30

        $Trigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today.AddHours($hour).AddMinutes($minute))
        $Triggers += $Trigger
    }
}

# Create action
$Action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory "D:\Projects\Amazfit Watch Project"

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# Register the task
Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Trigger $Triggers -Action $Action -Settings $Settings -Principal $Principal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Task Scheduler Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Task Name: $TaskName"
Write-Host "Schedule: Every 30 minutes from 8:00 AM to 2:00 PM"
Write-Host ""
Write-Host "The system will:"
Write-Host "  1. Check if you've woken up"
Write-Host "  2. When wake detected, wait 30 mins for data sync"
Write-Host "  3. Generate and send your daily report"
Write-Host "  4. Stop checking until tomorrow"
Write-Host ""
Write-Host "To view/modify: Open Task Scheduler > Task Scheduler Library > $TaskName"
Write-Host ""
