import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Briefcase, Building, MapPin, Calendar, Tag, ExternalLink } from "lucide-react";
import { getJobDetails } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface JobDetail {
  job_id: string;
  title: string;
  company: string;
  description: string;
  location?: string;
  posted_date?: string;
  role_key: string;
  seniority_level?: string;
  employment_type?: string;
  job_function?: string;
  industries?: string;
  role_tag?: string;
  job_url?: string;
  skills?: string[];
}

export default function JobDetailPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  
  const [job, setJob] = useState<JobDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    fetchJobDetails();
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getJobDetails(jobId!) as any;
      setJob(data);
    } catch (err: any) {
      setError({ message: err.message || "Failed to load job details" });
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spinner />;
  if (error) return <ErrorAlert error={error} />;
  if (!job) return <ErrorAlert error={{ message: "Job not found" }} />;

  return (
    <div className="container mx-auto max-w-5xl p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button 
          variant="ghost" 
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        {job.job_url && (
          <Button
            onClick={() => window.open(job.job_url, '_blank')}
            className="gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Apply on LinkedIn
          </Button>
        )}
      </div>

      {/* Job Header */}
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full font-medium">
                  {job.role_key}
                </span>
                {job.seniority_level && (
                  <span className="text-xs px-2 py-1 bg-secondary rounded-full">
                    {job.seniority_level}
                  </span>
                )}
                {job.employment_type && (
                  <span className="text-xs px-2 py-1 bg-secondary rounded-full">
                    {job.employment_type}
                  </span>
                )}
              </div>
              <CardTitle className="text-3xl mb-2">{job.title}</CardTitle>
              <div className="flex flex-wrap items-center gap-4 text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Building className="w-4 h-4" />
                  <span className="font-medium">{job.company}</span>
                </div>
                {job.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    <span>{job.location}</span>
                  </div>
                )}
                {job.posted_date && (
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(job.posted_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Job Description */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            Job Description
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <p className="whitespace-pre-line text-muted-foreground leading-relaxed">
              {job.description}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Skills Required */}
      {job.skills && job.skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Required Skills ({job.skills.length})
            </CardTitle>
            <CardDescription>
              Technical skills and technologies mentioned in this job posting
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {job.skills.map((skill, index) => (
                <span 
                  key={index}
                  className="px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-medium border border-primary/20"
                >
                  {skill}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Additional Info */}
      <Card>
        <CardHeader>
          <CardTitle>Additional Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {job.job_function && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground mb-1">Job Function</dt>
                <dd className="text-sm">{job.job_function}</dd>
              </div>
            )}
            {job.industries && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground mb-1">Industries</dt>
                <dd className="text-sm">{job.industries}</dd>
              </div>
            )}
            {job.role_tag && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground mb-1">Role Category</dt>
                <dd className="text-sm">{job.role_tag}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Footer Actions */}
      <div className="flex justify-between items-center pt-4">
        <Button
          variant="outline"
          onClick={() => navigate(-1)}
        >
          Back to Previous Page
        </Button>
        {job.job_url && (
          <Button
            onClick={() => window.open(job.job_url, '_blank')}
            className="gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Apply Now
          </Button>
        )}
      </div>
    </div>
  );
}
