# Сброс пароля админа (PowerShell)
# Использование: .\reset_admin_password.ps1
# Перед запуском: задайте ADMIN_RESET_SECRET в Railway Variables и задеплойте.

$url = "https://ai-tutor-platform-main-main-production.up.railway.app/auth/reset-admin-password"
$secret = "Presetapdmin2026"   # Должен совпадать с ADMIN_RESET_SECRET в Railway
$newPassword = "Skgfehi21?024ufn"

$body = @{ secret = $secret; new_password = $newPassword } | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body $body
    Write-Host "Пароль сброшен. Войдите с email:" $response.email "и паролем:" $newPassword
} catch {
    Write-Host "Ошибка:" $_.Exception.Message
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
}
