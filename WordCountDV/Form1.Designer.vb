<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class Form1
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Me.btnCount = New System.Windows.Forms.Button()
        Me.lblCount = New System.Windows.Forms.Label()
        Me.btnClear = New System.Windows.Forms.Button()
        Me.txtEntry = New System.Windows.Forms.TextBox()
        Me.SuspendLayout()
        '
        'btnCount
        '
        Me.btnCount.Location = New System.Drawing.Point(84, 253)
        Me.btnCount.Name = "btnCount"
        Me.btnCount.Size = New System.Drawing.Size(75, 34)
        Me.btnCount.TabIndex = 0
        Me.btnCount.Text = "Count"
        Me.btnCount.UseVisualStyleBackColor = True
        '
        'lblCount
        '
        Me.lblCount.AutoSize = True
        Me.lblCount.Location = New System.Drawing.Point(203, 255)
        Me.lblCount.Name = "lblCount"
        Me.lblCount.Size = New System.Drawing.Size(18, 20)
        Me.lblCount.TabIndex = 1
        Me.lblCount.Text = "0"
        '
        'btnClear
        '
        Me.btnClear.Location = New System.Drawing.Point(299, 252)
        Me.btnClear.Name = "btnClear"
        Me.btnClear.Size = New System.Drawing.Size(81, 35)
        Me.btnClear.TabIndex = 2
        Me.btnClear.Text = "Clear"
        Me.btnClear.UseVisualStyleBackColor = True
        '
        'txtEntry
        '
        Me.txtEntry.Font = New System.Drawing.Font("Microsoft Sans Serif", 10.0!, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, CType(0, Byte))
        Me.txtEntry.Location = New System.Drawing.Point(160, 131)
        Me.txtEntry.Name = "txtEntry"
        Me.txtEntry.Size = New System.Drawing.Size(100, 30)
        Me.txtEntry.TabIndex = 3
        '
        'Form1
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(9.0!, 20.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(478, 409)
        Me.Controls.Add(Me.txtEntry)
        Me.Controls.Add(Me.btnClear)
        Me.Controls.Add(Me.lblCount)
        Me.Controls.Add(Me.btnCount)
        Me.Name = "Form1"
        Me.Text = "Word Count "
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub
    Friend WithEvents btnCount As System.Windows.Forms.Button
    Friend WithEvents lblCount As System.Windows.Forms.Label
    Friend WithEvents btnClear As System.Windows.Forms.Button
    Friend WithEvents txtEntry As System.Windows.Forms.TextBox

End Class
