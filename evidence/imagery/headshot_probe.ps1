# Can we put a face in a player box? MEASURED, on a machine that can reach the CDN.
#
# WHY THIS FILE EXISTS. sleeper_import_report._headshot_probe already asks this question and
# asks it well. It was run once, on the owner's machine, and its answer was never written down
# -- so the repository still cannot say what happened. That is #37's failure shape (completion
# evidence that cannot be located), and the remedy is not to re-run it from memory but to give
# the run a FILE to land in. Run this, then commit headshot_probe_result.json beside it.
#
# WHY NOT JUST RUN THE PYTHON PROBE. It calls client.get_players() first, which needs
# api.sleeper.app -- blocked from the session environment (#143, 403 at CONNECT) and an
# unnecessary dependency for this question anyway. The player ids below are REAL, read out of
# data/fixtures/sleeper_capture.json, so the CDN is the only host this touches.
#
# ABSENCE IS NOT FLATTENED, exactly as the Python probe insists. "This player has no photo"
# (a 404) and "the fetch failed" (DNS, TLS, proxy, timeout) are different facts and are
# counted separately. A run that errors on all six says NOTHING about whether headshots exist.

$ids = @('96','138','19','260','421','827')   # Rodgers, Roethlisberger, Flacco, Johnson, Stafford, Taylor
$results = @()
foreach ($id in $ids) {
  foreach ($kind in @('full','thumb')) {
    $url = if ($kind -eq 'thumb') {
      "https://sleepercdn.com/content/nfl/players/thumb/$id.jpg"
    } else {
      "https://sleepercdn.com/content/nfl/players/$id.jpg"
    }
    $row = [ordered]@{ player_id = $id; kind = $kind; url = $url }
    try {
      # -UseBasicParsing: without it PowerShell hands the response to the Internet Explorer
      # HTML engine and prompts 'Script Execution Risk' on every single request. Harmless
      # here -- these are HEAD requests for .jpg, so there is no markup to parse -- but a
      # probe that stops twelve times to ask permission is a probe nobody finishes running.
      $r = Invoke-WebRequest -Uri $url -Method Head -TimeoutSec 20 -UseBasicParsing -ErrorAction Stop
      $row.outcome      = 'http'
      $row.status       = $r.StatusCode
      $row.content_type = $r.Headers['Content-Type']
      $row.bytes        = $r.Headers['Content-Length']
    } catch [System.Net.WebException] {
      # A 404 IS an answer -- "no headshot for that player". Keep it out of the error bucket.
      $resp = $_.Exception.Response
      if ($resp) { $row.outcome = 'http'; $row.status = [int]$resp.StatusCode }
      else       { $row.outcome = 'fetch_error'; $row.error = $_.Exception.Message }
    } catch {
      $row.outcome = 'fetch_error'; $row.error = $_.Exception.Message
    }
    $results += [pscustomobject]$row
  }
}

$results | Format-Table -AutoSize

$ok      = @($results | Where-Object { $_.outcome -eq 'http' -and $_.status -eq 200 }).Count
$notfound= @($results | Where-Object { $_.outcome -eq 'http' -and $_.status -ne 200 }).Count
$errored = @($results | Where-Object { $_.outcome -eq 'fetch_error' }).Count

$verdict = if ($errored -eq $results.Count) {
  'INCONCLUSIVE -- every fetch errored. This says nothing about whether headshots exist.'
} elseif ($ok -gt 0) {
  'headshots ARE available at this pattern'
} else {
  'no headshot resolved on any sampled player -- do NOT wire photos on this evidence'
}

$out = [ordered]@{
  measured_utc              = (Get-Date).ToUniversalTime().ToString('o')
  checked                   = $results.Count
  headshot_returned_200     = $ok
  no_headshot_for_that_player = $notfound
  fetch_errored             = $errored
  verdict                   = $verdict
  results                   = $results
}
$path = Join-Path $PSScriptRoot 'headshot_probe_result.json'
$out | ConvertTo-Json -Depth 6 | Set-Content -Path $path -Encoding UTF8
Write-Host ""
Write-Host "VERDICT: $verdict"
Write-Host "wrote $path"
