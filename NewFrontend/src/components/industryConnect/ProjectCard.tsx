import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ProjectRecommendation } from '@/types/industryConnect';

interface ProjectCardProps {
  project: ProjectRecommendation;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{project.project_title || 'Capstone Project'}</CardTitle>
        {project.objective && (
          <p className="text-sm text-muted-foreground italic">{project.objective}</p>
        )}
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="tech-stack">
          <TabsList>
            <TabsTrigger value="tech-stack">Tech Stack</TabsTrigger>
            <TabsTrigger value="steps">Implementation Steps</TabsTrigger>
          </TabsList>
          <TabsContent value="tech-stack" className="pt-4">
            {project.tech_stack && project.tech_stack.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {project.tech_stack.map((tech, i) => {
                  const clean = tech.replace(/^[-*>]\s*/, '').trim();
                  return clean ? (
                    <Badge key={i} variant="secondary">
                      {clean}
                    </Badge>
                  ) : null;
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No specific tech stack listed.</p>
            )}
          </TabsContent>
          <TabsContent value="steps" className="pt-4">
            {project.implementation_steps && project.implementation_steps.length > 0 ? (
              <ol className="space-y-3">
                {project.implementation_steps.map((step, i) => {
                  const clean = step.replace(/^\d+[.):\-]\s*/, '').trim();
                  return (
                    <li key={i} className="text-sm">
                      <span className="font-semibold">{i + 1}.</span> {clean}
                    </li>
                  );
                })}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">No steps available.</p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
