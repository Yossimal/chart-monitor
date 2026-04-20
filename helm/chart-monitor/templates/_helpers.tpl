{{/*
Expand the name of the chart.
*/}}
{{- define "chart-monitor.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "chart-monitor.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Backend fully qualified name.
*/}}
{{- define "chart-monitor.backend.fullname" -}}
{{- printf "%s-backend" (include "chart-monitor.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Frontend fully qualified name.
*/}}
{{- define "chart-monitor.frontend.fullname" -}}
{{- printf "%s-frontend" (include "chart-monitor.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "chart-monitor.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to all resources.
*/}}
{{- define "chart-monitor.labels" -}}
helm.sh/chart: {{ include "chart-monitor.chart" . }}
{{ include "chart-monitor.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels (used by Deployments and Services).
*/}}
{{- define "chart-monitor.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart-monitor.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend selector labels.
*/}}
{{- define "chart-monitor.backend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart-monitor.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend selector labels.
*/}}
{{- define "chart-monitor.frontend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart-monitor.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Name of the Secret to load (existingSecret or chart fullname).
*/}}
{{- define "chart-monitor.secretName" -}}
{{- if .Values.existingSecret }}
{{- .Values.existingSecret }}
{{- else }}
{{- include "chart-monitor.fullname" . }}
{{- end }}
{{- end }}

{{/*
ServiceAccount name.
*/}}
{{- define "chart-monitor.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "chart-monitor.fullname" . }}
{{- end }}
{{- end }}
