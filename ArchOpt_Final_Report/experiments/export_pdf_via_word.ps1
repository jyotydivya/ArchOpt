$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

$docxPath = "e:\ArchOpt\ArchOpt_Final_Report\ArchOpt_Final_Project_Report.docx"
$pdfPath = "e:\ArchOpt\ArchOpt_Final_Report\ArchOpt_Final_Project_Report.pdf"

try {
    Write-Host "Opening document in Word: $docxPath"
    $doc = $word.Documents.Open($docxPath, $false, $true)
    Write-Host "Updating all document fields..."
    $doc.Fields.Update()
    Write-Host "Updating Tables of Contents..."
    foreach ($toc in $doc.TablesOfContents) {
        $toc.Update()
    }
    Write-Host "Exporting native PDF: $pdfPath"
    $wdFormatPDF = 17
    $doc.SaveAs([ref]$pdfPath, [ref]$wdFormatPDF)
    $doc.Close($false)
    Write-Host "[SUCCESS] Native Word PDF exported successfully!"
} catch {
    Write-Host "[ERROR] Failed during Word export: $($_.Exception.Message)"
} finally {
    $word.Quit()
}

