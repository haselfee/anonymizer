{{- define "anonymizer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "anonymizer.fullname" -}}
{{- include "anonymizer.name" . -}}
{{- end -}}

{{- define "anonymizer.labels" -}}
app.kubernetes.io/name: {{ include "anonymizer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
{{- end -}}
