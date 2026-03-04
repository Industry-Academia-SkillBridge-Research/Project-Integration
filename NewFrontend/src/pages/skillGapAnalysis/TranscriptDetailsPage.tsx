import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { FileText, ArrowRight, ArrowLeft } from "lucide-react";
import { getTranscript } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface Course {
  course_code: string;
  course_name: string;
  grade: string;
  credits: number | string;
}

interface TranscriptData {
  student_id: string;
  name: string;
  program: string;
  intake: string;
  specialization: string;
  courses: Course[];
}

export default function TranscriptDetailsPage() {
  const navigate = useNavigate();
  const { studentId } = useParams();
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    const fetchTranscript = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await getTranscript(studentId!) as TranscriptData;
        setTranscript(data);
      } catch (err: any) {
        setError(err.response?.data || { message: err.message });
      } finally {
        setLoading(false);
      }
    };

    fetchTranscript();
  }, [studentId]);

  if (loading) return <Spinner />;
  if (error) return (
    <div className="min-h-screen bg-gradient-hero">
      <div className="container mx-auto max-w-4xl p-6">
        <ErrorAlert error={error} />
        <div className="mt-4 flex justify-center">
          <Button onClick={() => navigate(`/skill-gap-analysis/${studentId}/upload`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Upload
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(`/skill-gap-analysis/${studentId}/upload`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Upload New Transcript
          </Button>
          <h1 className="text-xl font-bold text-foreground">Transcript Details</h1>
          <div className="w-40" /> {/* Spacer */}
        </nav>
      </header>

      {/* Main Content */}
      <div className="container mx-auto max-w-6xl px-6 pb-12 space-y-6">
        <Card className="shadow-elevated animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-6 w-6" />
              Transcript Details
            </CardTitle>
            <CardDescription>
              Extracted information from your academic transcript
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Student ID</p>
                <p className="text-lg font-semibold">{transcript?.student_id || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Name</p>
                <p className="text-lg font-semibold">{transcript?.name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Program</p>
                <p className="text-lg font-semibold">{transcript?.program || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Intake</p>
                <p className="text-lg font-semibold">{transcript?.intake || 'N/A'}</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Field of Specialization</p>
                <p className="text-lg font-semibold">{transcript?.specialization || 'N/A'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-elevated animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <CardHeader>
            <CardTitle>Courses</CardTitle>
            <CardDescription>
              List of courses extracted from your transcript
            </CardDescription>
          </CardHeader>
          <CardContent>
            {transcript?.courses && transcript.courses.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Course Code</TableHead>
                    <TableHead>Course Name</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>Credits</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transcript.courses.map((course, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{course.course_code || 'N/A'}</TableCell>
                      <TableCell>{course.course_name || 'N/A'}</TableCell>
                      <TableCell>{course.grade || 'N/A'}</TableCell>
                      <TableCell>{course.credits || 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground">No courses found</p>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button
            onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}
            size="lg"
            className="gap-2"
          >
            View Skills
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
