import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { uploadJobDescription } from "@/services/nilmaniService";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import "../styles/interview.css";

const UploadJDPage = () => {
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const formatBytes = (bytes: number): string => {
    if (!bytes) return "";
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.min(
      Math.floor(Math.log(bytes) / Math.log(1024)),
      sizes.length - 1
    );
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const handleFileObject = async (file: File | null | undefined) => {
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file");
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    setError(null);
    setUploading(true);
    setFileName(file.name);
    setFileSize(file.size);

    try {
      const response = await uploadJobDescription(file);

      // Store session data
      localStorage.setItem("nilmani_sessionId", response.session_id);
      localStorage.setItem("nilmani_jdText", response.text);
      localStorage.setItem("nilmani_chunksCount", response.chunks_count.toString());

      // Navigate to interview page
      setTimeout(() => {
        navigate("/interview-prep/interview");
      }, 800);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Upload failed. Please try again."
      );
      setFileName(null);
      setFileSize(null);
    } finally {
      setUploading(false);
    }
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    handleFileObject(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    handleFileObject(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const openFilePicker = () => {
    inputRef.current?.click();
  };

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div>
          <div className="interview-eyebrow">Step 1 of 2</div>
          <h1 className="interview-title">Upload Job Description</h1>
          <p className="interview-lead">
            Upload the job description PDF to start your AI-powered interview
            training
          </p>
        </div>
      </div>

      <div className="interview-upload-container">
        <Card
          className={`interview-drop-zone ${dragOver ? "drag-over" : ""} ${
            uploading ? "uploading" : ""
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={openFilePicker}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            onChange={handleFile}
            style={{ display: "none" }}
          />

          {uploading ? (
            <div className="interview-upload-status">
              <Loader2 className="w-12 h-12 animate-spin text-primary" />
              <p className="interview-upload-text">
                Processing job description...
              </p>
            </div>
          ) : fileName ? (
            <div className="interview-upload-status success">
              <CheckCircle className="w-12 h-12 text-success" />
              <p className="interview-upload-text">{fileName}</p>
              <p className="interview-upload-subtext">{formatBytes(fileSize!)}</p>
              <p className="interview-upload-hint">Redirecting to interview...</p>
            </div>
          ) : (
            <div className="interview-drop-zone-content">
              <FileText className="w-16 h-16 text-muted-foreground mb-4" />
              <p className="interview-drop-zone-text">
                <strong>Click to browse</strong> or drag and drop
              </p>
              <p className="interview-drop-zone-hint">PDF files only • Max 10MB</p>
            </div>
          )}
        </Card>

        {error && (
          <div className="interview-error-box">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadJDPage;
