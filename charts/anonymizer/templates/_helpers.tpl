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

{{/* decides if the first path segment looks like a registry (has '.' or ':' or 'localhost') */}}
{{- define "anonymizer._hasRegistry" -}}
{{- $first := (splitList "/" .repository | first) -}}
{{- if or (contains "." $first) (contains ":" $first) (eq $first "localhost") -}}true{{- else -}}false{{- end -}}
{{- end -}}

{{/* Safe image builder: only prefix when non-empty */}}
{{- define "anonymizer.image" -}}
{{- $prefix := default "" .Values.global.imageRegistry -}}
{{- $repo   := .repository -}}
{{- $tag    := .tag -}}
{{- if ne $prefix "" -}}
{{- printf "%s/%s:%s" $prefix $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end -}}