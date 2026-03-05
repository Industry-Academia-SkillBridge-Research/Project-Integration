import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { uploadJobDescription } from "../services/api";

function UploadJDPage() {
  const [fileName, setFileName] = useState(null);
  const [fileSize, setFileSize] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const inputRef = useRef();

  const formatBytes = (bytes) => {
    if (!bytes) return "";
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const handleFileObject = async (file) => {
    if (!file) return;
    
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError("Please upload a PDF file");
      return;
    }

    setError(null);
    setUploading(true);
    setFileName(file.name);
    setFileSize(file.size);

    try {
      const response = await uploadJobDescription(file);
      
      // Store session data
      localStorage.setItem('sessionId', response.session_id);
      localStorage.setItem('jdText', response.text);
      localStorage.setItem('chunksCount', response.chunks_count);
      
      // Navigate to interview page
      setTimeout(() => {
        navigate("/interview");
      }, 800);
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
      setFileName(null);
      setFileSize(null);
    } finally {
      setUploading(false);
    }
  };

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    handleFileObject(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    handleFileObject(file);
  };

  const handleDragOver = (e) => {
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
    <div className="page">
      <div className="page-header">
        <div>
          <div className="eyebrow">Step 1 of 2</div>
          <h1>Upload Job Description</h1>
          <p className="lead">
            Upload the job description PDF to start your AI-powered interview training
          </p>
        </div>
      </div>

      <div className="upload-container">
        <div
          className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploading ? "uploading" : ""}`}
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
            <div className="upload-status">
              <div className="spinner"></div>
              <p className="upload-text">Processing job description...</p>
              {/* <p className="upload-subtext">Creating embeddings and initializing RAG system</p> */}
            </div>
          ) : fileName ? (
            <div className="upload-status success">
              <div className="success-icon">✓</div>
              <p className="upload-text">{fileName}</p>
              <p className="upload-subtext">{formatBytes(fileSize)}</p>
              <p className="upload-hint">Redirecting to interview...</p>
            </div>
          ) : (
            <div className="drop-zone-content">
              <div className="upload-icon">📄</div>
              <p className="drop-zone-text">
                <strong>Click to browse</strong> or drag and drop
              </p>
              <p className="drop-zone-hint">PDF files only • Max 10MB</p>
            </div>
          )}
        </div>

        {error && (
          <div className="error-box">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadJDPage;
