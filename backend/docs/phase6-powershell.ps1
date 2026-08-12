$base = "http://localhost:8000"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

$csrf = Invoke-RestMethod -Method Get -Uri "$base/api/auth/csrf" `
    -WebSession $session
$headers = @{ "X-CSRF-Token" = $csrf.csrf_token }

$email = Read-Host "Correo"
$password = Read-Host "Contraseña"
$loginBody = @{
    email = $email
    password = $password
    remember_me = $false
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/auth/login" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $loginBody
$me = Invoke-RestMethod -Method Get -Uri "$base/api/auth/me" `
    -WebSession $session

$clientBody = @{
    document_type = "RUC"
    document_number = "20609999001"
    business_name = "Cliente Ficticio Swagger S.A.C."
    contact_name = "Contacto Ficticio"
    email = "contacto@example.com"
    phone = "900000000"
    address = "Av. Pruebas 123"
    district = "Ate"
    province = "Lima"
    department = "Lima"
} | ConvertTo-Json
$client = Invoke-RestMethod -Method Post -Uri "$base/api/clients" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $clientBody

$shipmentBody = @{
    client_id = $client.id
    origin_address = "Centro de distribución Lima"
    destination_address = "Av. Destino 456"
    origin_district = "Ate"
    destination_district = "Miraflores"
    package_description = "Paquete ficticio"
    package_count = 2
    total_weight = 4.5
    declared_value = 150
    priority = "normal"
} | ConvertTo-Json
$shipment = Invoke-RestMethod -Method Post -Uri "$base/api/shipments" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $shipmentBody

$statusBody = @{
    status = "pending_pickup"
    description = "Recojo programado"
    location = "Lima"
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri "$base/api/shipments/$($shipment.id)/status" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $statusBody

$warehouseBody = @{
    code = "LIM-PS-01"
    name = "Almacén PowerShell"
    address = "Av. Almacén 100"
    district = "Ate"
    province = "Lima"
    department = "Lima"
    capacity = 1000
} | ConvertTo-Json
$warehouse = Invoke-RestMethod -Method Post -Uri "$base/api/warehouses" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $warehouseBody

$itemBody = @{
    warehouse_id = $warehouse.id
    sku = "PS-SKU-001"
    name = "Caja de prueba"
    current_stock = 10
    minimum_stock = 5
    unit = "unidad"
} | ConvertTo-Json
$item = Invoke-RestMethod -Method Post -Uri "$base/api/inventory" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $itemBody

$movementBody = @{
    inventory_item_id = $item.id
    movement_type = "entry"
    quantity = 3
    reason = "Ingreso de prueba"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/inventory/movements" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $movementBody

$routeBody = @{
    route_code = "PS-RUTA-001"
    name = "Ruta PowerShell"
    origin = "Lima"
    destination = "Callao"
    scheduled_date = (Get-Date).ToString("yyyy-MM-dd")
    status = "planned"
} | ConvertTo-Json
$route = Invoke-RestMethod -Method Post -Uri "$base/api/routes" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $routeBody

$assignmentBody = @{
    shipment_ids = @($shipment.id)
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri "$base/api/routes/$($route.id)/assign-shipments" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $assignmentBody

$incidentBody = @{
    shipment_id = $shipment.id
    incident_type = "delay"
    title = "Retraso ficticio"
    description = "Incidencia creada para una prueba manual."
    severity = "medium"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/incidents" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $incidentBody

$participantBody = @{ linked_user_id = $me.user.id } | ConvertTo-Json
$participant = Invoke-RestMethod -Method Post `
    -Uri "$base/api/research/participants" -WebSession $session `
    -Headers $headers -ContentType "application/json" -Body $participantBody

$consentBody = @{
    participant_id = $participant.id
    consent_version = "v1-demo"
    accepted = $true
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/api/research/consent" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $consentBody

$startBody = @{
    participant_id = $participant.id
    scenario = "register_shipment"
    expected_duration_minutes = 10
    client_timezone = "America/Lima"
    screen_width = 1920
    screen_height = 1080
    browser = "Chrome"
    operating_system = "Windows"
    device_type = "desktop"
} | ConvertTo-Json
$experiment = Invoke-RestMethod -Method Post `
    -Uri "$base/api/research/sessions/start" -WebSession $session `
    -Headers $headers -ContentType "application/json" -Body $startBody

# PowerShell 7: indique una imagen JPEG o WebP ficticia menor de 1 MiB.
$imagePath = Read-Host "Ruta local de JPEG/WebP de prueba"
$imageWidth = [int](Read-Host "Ancho real de la imagen")
$imageHeight = [int](Read-Host "Alto real de la imagen")
$captureForm = @{
    image = Get-Item $imagePath
    captured_at = (Get-Date).ToUniversalTime().ToString("o")
    sequence_number = 1
    width = $imageWidth
    height = $imageHeight
    visibility_state = "visible"
    client_timezone_offset = -300
}
Invoke-RestMethod -Method Post `
    -Uri "$base/api/research/sessions/$($experiment.session.id)/face-captures" `
    -WebSession $session -Headers $headers -Form $captureForm

$batchId = [guid]::NewGuid().ToString()
$now = (Get-Date).ToUniversalTime()
$batchBody = @{
    batch_id = $batchId
    sequence_number = 1
    started_at = $now.ToString("o")
    ended_at = $now.AddSeconds(3).ToString("o")
    events = @(
        @{
            type = "keyboard"
            event = "timing"
            category = "alphanumeric"
            dwell_time_ms = 85
            flight_time_ms = 120
            timestamp = $now.AddSeconds(1).ToString("o")
            sequence_index = 1
        },
        @{
            type = "mouse"
            event = "move"
            normalized_x = 0.42
            normalized_y = 0.61
            timestamp = $now.AddSeconds(2).ToString("o")
            sequence_index = 2
        }
    )
} | ConvertTo-Json -Depth 8
Invoke-RestMethod -Method Post `
    -Uri "$base/api/research/sessions/$($experiment.session.id)/behavior-batches" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $batchBody

Invoke-RestMethod -Method Get `
    -Uri "$base/api/research/sessions/$($experiment.session.id)" `
    -WebSession $session

$finishBody = @{
    client_ended_at = (Get-Date).ToUniversalTime().ToString("o")
    client_error_count = 0
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
    -Uri "$base/api/research/sessions/$($experiment.session.id)/finish" `
    -WebSession $session -Headers $headers -ContentType "application/json" `
    -Body $finishBody
