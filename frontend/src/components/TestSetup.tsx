import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export const TestSetup = () => {
  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold mb-4">shadcn Setup Test</h2>
      <p className="text-muted-foreground mb-4">
        If you can see this, the shadcn components are properly configured!
      </p>
      <Button>Test Button</Button>
    </Card>
  );
};
