import { AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./card";

interface ErrorAlertProps {
  error: any;
}

export function ErrorAlert({ error }: ErrorAlertProps) {
  // Extract error message from various error formats
  const getErrorMessage = () => {
    if (typeof error === 'string') return error;
    if (error?.detail) return typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
    if (error?.message) return error.message;
    if (error?.error) return error.error;
    return JSON.stringify(error) || "An error occurred. Please try again.";
  };

  return (
    <Card className="border-destructive">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          Error
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-destructive whitespace-pre-wrap">
          {getErrorMessage()}
        </p>
      </CardContent>
    </Card>
  );
}
