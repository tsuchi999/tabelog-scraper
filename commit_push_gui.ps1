Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

$msg = [Microsoft.VisualBasic.Interaction]::InputBox("Enter commit message:", "Git Commit")

if ($msg -eq "") {
    [System.Windows.Forms.MessageBox]::Show("Canceled", "Exit") | Out-Null
    exit
}

git add .
git commit -m "$msg"

$result = [System.Windows.Forms.MessageBox]::Show("Do you want to push?", "Push Confirmation", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)

if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
    git push
    [System.Windows.Forms.MessageBox]::Show("Push complete!", "Done") | Out-Null
} else {
    [System.Windows.Forms.MessageBox]::Show("Push skipped.", "Skipped") | Out-Null
}
