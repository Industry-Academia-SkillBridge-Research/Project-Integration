import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Upload, CheckCircle2, ArrowLeft } from "lucide-react";
import { uploadTranscript } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

export default function TranscriptUploadPage() {
  const navigate = useNavigate();
  const { studentId } = useParams();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (!validTypes.includes(selectedFile.type)) {
        setError({ message: 'Please select a PDF or image file (PNG, JPG)' });
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError({ message: 'Please select a file first' });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await uploadTranscript(studentId!, file);
      navigate(`/skill-gap-analysis/${studentId}/transcript`);
    } catch (err: any) {
      console.error('Upload error:', err);
      const errorData = err.response?.data || err;
      setError(errorData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate('/modules')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Modules
          </Button>
          <h1 className="text-xl font-bold text-foreground">Skill Gap Analysis Workflow</h1>
          <div className="w-24" /> {/* Spacer for alignment */}
        </nav>
      </header>

      {/* Main Content */}
      <div className="container mx-auto max-w-3xl px-6 pb-12">
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-foreground mb-2">Upload Your Transcript</h2>
          <p className="text-muted-foreground">Begin your skill validation journey by uploading your academic transcript</p>
        </div>
        
        <Card className="border-primary/20 shadow-elevated">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto mb-4 w-16 h-16 bg-gradient-to-br from-primary to-accent rounded-2xl flex items-center justify-center">
              <Upload className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl">Upload Transcript</CardTitle>
            <CardDescription className="text-base">
              Upload your academic transcript (PDF or image file) to begin skill validation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && <ErrorAlert error={error} />}
            
            <div className="space-y-3">
              <label htmlFor="file" className="text-sm font-semibold text-foreground">
                Select Transcript File
              </label>
              <div className="relative">
                <Input
                  id="file"
                  type="file"
                  accept=".pdf,image/png,image/jpeg,image/jpg"
                  onChange={handleFileChange}
                  disabled={loading}
                  className="cursor-pointer file:cursor-pointer file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-white hover:file:bg-primary/90"
                />
              </div>
              {file && (
                <div className="flex items-center gap-2 p-3 bg-primary/5 border border-primary/20 rounded-lg">
                  <CheckCircle2 className="h-5 w-5 text-primary" />
                  <p className="text-sm font-medium text-foreground">
                    {file.name} <span className="text-muted-foreground">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                  </p>
                </div>
              )}
            </div>

            {loading ? (
              <div className="flex justify-center py-4">
                <Spinner />
              </div>
            ) : (
              <>
                <Button
                  onClick={handleUpload}
                  disabled={!file}
                  className="w-full gap-2"
                  size="lg"
                >
                  <Upload className="h-5 w-5" />
                  Upload & Analyze Transcript
                </Button>
                
                <p className="text-xs text-center text-muted-foreground mt-3">
                  Supported formats: PDF, PNG, JPG • Maximum size: 10MB
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
