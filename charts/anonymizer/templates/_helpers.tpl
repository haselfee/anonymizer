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

{{- define "anonymizer.image" -}}
{{- $registry := required "image.registry is required" .Values.image.registry -}}
{{- $groupProject := required "image.groupProject is required" .Values.image.groupProject -}}
{{- $repo := required "repository is required" .repository -}}
{{- $tag  := default "latest" .tag -}}
{{- printf "%s/%s/%s:%s" $registry $groupProject $repo $tag -}}
{{- end -}}