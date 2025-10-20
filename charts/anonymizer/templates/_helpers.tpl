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

{{/* Detect if repository already contains a registry (first path segment has '.' or ':' or equals 'localhost') */}}
{{- define "anonymizer._hasRegistry" -}}
{{- $first := (index (splitList "/" .repository) 0) -}}
{{- if or (contains "." $first) (contains ":" $first) (eq $first "localhost") -}}true{{- else -}}false{{- end -}}
{{- end -}}

{{/* Build image string safely. Prefix with global.imageRegistry only if non-empty AND repo has no registry */}}
{{- define "anonymizer.image" -}}
{{- $vals    := .Values           | default (dict) -}}
{{- $global  := $vals.global      | default (dict) -}}
{{- $prefix  := $global.imageRegistry | default "" -}}
{{- $repo    := .repository -}}
{{- $tag     := .tag | default "latest" -}}
{{- $hasReg  := (include "anonymizer._hasRegistry" (dict "repository" $repo)) | eq "true" -}}
{{- if and $prefix (ne $prefix "") (not $hasReg) -}}
{{- printf "%s/%s:%s" $prefix $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end -}}
