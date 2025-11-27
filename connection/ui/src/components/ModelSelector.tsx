import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";

const AI_MODELS = [
  { id: "baseline-llava", name: "Baseline-LLaVA", description: "Baseline VLM for CAD code generation" },
  { id: "qwen-2.5-xb", name: "Qwen-2.5-xB", description: "Next-gen VLM for CAD code generation (x billion # of parameters)" },
];

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
}

export function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
  const currentModel = AI_MODELS.find(model => model.id === selectedModel);
  
  return (
    <div className="w-64">
      <Select value={selectedModel} onValueChange={onModelChange}>
        <SelectTrigger className="bg-muted border-border">
          <SelectValue placeholder="Select a model">
            {currentModel?.name}
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="bg-card border-border">
          {AI_MODELS.map((model) => (
            <SelectItem key={model.id} value={model.id}>
              <div className="flex flex-col items-start">
                <span>{model.name}</span>
                <span className="text-muted-foreground text-sm">{model.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}