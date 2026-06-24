Option Explicit
Dim texto
Dim voz

Do
    texto = InputBox("Escribe algo para que lo diga la voz:", "Texto a voz")
    If texto <> "" Then
        Set voz = CreateObject("SAPI.SpVoice")
        voz.Speak texto
        Set voz = Nothing
        If MsgBox("ùDesea hacer lo mismo que antes?", vbOKCancel + vbQuestion, "Repetir") = vbCancel Then
            Exit Do
        End If
    Else
        Exit Do
    End If
Loop