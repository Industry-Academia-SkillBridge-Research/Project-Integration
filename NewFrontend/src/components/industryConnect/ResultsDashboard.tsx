import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AnalysisResult } from '@/types/industryConnect';
import SkillMatchScore from './SkillMatchScore';
import ProjectCard from './ProjectCard';

interface ResultsDashboardProps {
  result: AnalysisResult;
}

export default function ResultsDashboard({ result }: ResultsDashboardProps) {
  const { gap_analysis, project_recommendation } = result;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <h2 className="text-xl font-semibold">Analysis Result</h2>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SkillMatchScore score={gap_analysis.match_percentage} />

        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{gap_analysis.analysis_summary || 'No summary available.'}</p>
          </CardContent>
        </Card>
      </div>

      {/* Missing Skills */}
      {gap_analysis.missing_skills && gap_analysis.missing_skills.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Missing Skills</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {gap_analysis.missing_skills.map((skill, i) => (
              <Badge key={i} variant="destructive">{skill}</Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Project Recommendation */}
      <ProjectCard project={project_recommendation} />
    </div>
  );
}
