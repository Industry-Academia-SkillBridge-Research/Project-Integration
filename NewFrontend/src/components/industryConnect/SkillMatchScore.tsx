import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SkillMatchScoreProps {
  score: number;
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score < 50) return 'text-red-600';
  return 'text-yellow-600';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-50 border-green-200';
  if (score < 50) return 'bg-red-50 border-red-200';
  return 'bg-yellow-50 border-yellow-200';
}

export default function SkillMatchScore({ score }: SkillMatchScoreProps) {
  const safeScore = typeof score === 'string'
    ? parseInt(String(score).replace(/[^\d]/g, ''), 10) || 0
    : Number(score) || 0;

  return (
    <Card className={cn('border', getScoreBg(safeScore))}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Skill Match Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn('text-4xl font-bold', getScoreColor(safeScore))}>
          {safeScore}%
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {safeScore < 100 ? `${safeScore - 100}% gap` : 'Perfect match'}
        </p>
      </CardContent>
    </Card>
  );
}
