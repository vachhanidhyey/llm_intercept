Imports System.Char
Public Class Form1
    Inherits System.Windows.Forms.Form

    Private Sub btnClear_Click(ByVal sender As System.Object,
    ByVal e As System.EventArgs) Handles btnClear.Click
        txtEntry.Text = ""
        lblCount.Text = "0"
        txtEntry.Focus()
    End Sub

    ' This event handles "count" button click...
    Private Sub btnCount_Click(ByVal sender As System.Object, ByVal e As  _
    System.EventArgs) Handles btnCount.Click
        Dim J As Integer, Last As Integer = txtEntry.TextLength - 1
        Dim ThisChar As Char
        Dim InAWord As Boolean = False, WordCount As Integer = 0
        For J = 0 To Last  ' Chars collection is zero-based 
            ThisChar = txtEntry.Text.Chars(J)
            If IsLetter(ThisChar) Or ThisChar = "'" Then ' legal characters 
                If Not InAWord Then ' new word
                    WordCount += 1 ' add 1 to count
                End If
                InAWord = True
            Else      ' could be space, full stop, comma etc
                InAWord = False
            End If
        Next J
        lblCount.Text = WordCount

    End Sub

End Class


