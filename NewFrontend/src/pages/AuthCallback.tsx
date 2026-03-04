import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

const AuthCallback = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Extract token and error from URL query parameters
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get("token");
        const errorParam = urlParams.get("error");

        if (errorParam) {
          setError(errorParam);
          // Redirect to auth page after 3 seconds
          setTimeout(() => {
            navigate("/auth");
          }, 3000);
          return;
        }

        if (token) {
          // Store the token in localStorage
          localStorage.setItem("access_token", token);
          
          // Refresh auth state
          await checkAuth();
          
          // Redirect to modules page
          navigate("/modules");
        } else {
          setError("No token received from authentication");
          setTimeout(() => {
            navigate("/auth");
          }, 3000);
        }
      } catch (err) {
        console.error("Auth callback error:", err);
        setError("Authentication failed. Please try again.");
        setTimeout(() => {
          navigate("/auth");
        }, 3000);
      }
    };

    handleCallback();
  }, [navigate, checkAuth]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="text-center space-y-4">
        {error ? (
          <>
            <div className="text-red-500 text-xl font-semibold">
              Authentication Error
            </div>
            <p className="text-muted-foreground">{error}</p>
            <p className="text-sm text-muted-foreground">
              Redirecting to login page...
            </p>
          </>
        ) : (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
            <div className="text-xl font-semibold text-foreground">Completing authentication...</div>
            <p className="text-muted-foreground">Please wait while we log you in</p>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
