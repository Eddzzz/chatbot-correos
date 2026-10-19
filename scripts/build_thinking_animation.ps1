# Rebuild the transparent, 24 fps loading animation from the ImageGen poses.
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$spritePath = Join-Path $projectDirectory 'frontend/public/cartero-thinking-v2.png'
$videoPath = Join-Path $projectDirectory 'frontend/public/cartero-thinking-v2-24fps.webm'
$dimensions = (& ffprobe -v error -show_entries stream=width,height -of json $spritePath) | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Could not read sprite dimensions.' }
$cellWidth = $dimensions.streams[0].width / 6
$cellHeight = $dimensions.streams[0].height / 4
if ($cellWidth -ne $cellHeight -or $cellWidth % 1 -ne 0) { throw 'Expected six columns and four rows of square frames.' }
$poses = @(0..23) + @(0, 1) # Include the loop seam and blending lookahead.
$splitLabels = (0..25 | ForEach-Object { "[pose$_]" }) -join ''
$segments = @("[0:v]split=26$splitLabels")
for ($index = 0; $index -lt $poses.Count; $index++) {
  $column = $poses[$index] % 6
  $row = [math]::Floor($poses[$index] / 6)
  $segments += "[pose$index]crop=${cellWidth}:${cellHeight}:$($column * $cellWidth):$($row * $cellHeight),scale=320:320[frame$index]"
}
$frameLabels = (0..25 | ForEach-Object { "[frame$_]" }) -join ''
$segments += "${frameLabels}concat=n=26:v=1:a=0,settb=1/24,setpts=N*4,format=yuva444p,split=2[color][mask]"
# Subtle adjacent poses blend without optical-flow warping of the face and fingers.
$interpolation = 'framerate=fps=24:interp_start=0:interp_end=255:scene=100'
$segments += "[color]format=yuv420p,$interpolation[rgb]"
$segments += "[mask]alphaextract,format=yuv420p,$interpolation[alpha]"
$segments += '[rgb][alpha]alphamerge,setpts=PTS-STARTPTS,trim=duration=4,format=yuva420p[animation]'
& ffmpeg -hide_banner -loglevel warning -y -framerate 6 -i $spritePath -filter_complex ($segments -join ';') -map '[animation]' -an -r 24 -fps_mode cfr -frames:v 96 -c:v libvpx-vp9 -crf 25 -b:v 0 -auto-alt-ref 0 -metadata 'comment=24 ImageGen keyframes; gentle frame blending; 24 fps; 4 second loop' $videoPath
if ($LASTEXITCODE -ne 0) { throw 'Animation generation failed.' }
Write-Output $videoPath
