import * as React from "react";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { SkillMultiSelect } from "@/components/ui/multi-select-skills";

export function ManualResumeForm({ 
  onSubmit, 
  isSubmitting 
}: { 
  onSubmit: (data: any) => void;
  isSubmitting: boolean;
}) {
  const { register, control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      full_name: "",
      headline: "",
      summary: "",
      contact: {
        email: "",
        location: "",
        linkedin: "",
        github: ""
      },
      skills: [],
      projects: [{ name: "", description: "", link: "", technologies: [] }],
      experience: [],
      education: []
    }
  });

  const { fields: projectFields, append: appendProject, remove: removeProject } = useFieldArray({
    control,
    name: "projects"
  });

  const { fields: expFields, append: appendExp, remove: removeExp } = useFieldArray({
    control,
    name: "experience"
  });

  const { fields: eduFields, append: appendEdu, remove: removeEdu } = useFieldArray({
    control,
    name: "education"
  });

  const onFormSubmit = (data: any) => {
    if (!data.skills || data.skills.length === 0) {
      alert("Please add at least 1 skill.");
      return;
    }
    if (!data.projects || data.projects.length === 0 || !data.projects[0].name) {
      alert("Please add at least 1 valid project.");
      return;
    }
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-8 text-left mt-6">
      <div className="space-y-4">
        <h3 className="font-display text-xl font-semibold text-foreground">Basic Info</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="full_name">Full Name <span className="text-destructive">*</span></Label>
            <Input id="full_name" placeholder="John Doe" {...register("full_name", { required: true })} className={errors.full_name ? "border-destructive" : ""} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="headline">Headline</Label>
            <Input id="headline" placeholder="Software Engineer" {...register("headline")} />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="summary">Summary</Label>
          <Textarea id="summary" placeholder="A brief summary about yourself..." {...register("summary")} />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-display text-xl font-semibold text-foreground">Contact</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="john@example.com" {...register("contact.email")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="location">Location</Label>
            <Input id="location" placeholder="San Francisco, CA" {...register("contact.location")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="linkedin">LinkedIn URL</Label>
            <Input id="linkedin" placeholder="https://linkedin.com/in/johndoe" {...register("contact.linkedin")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="github">GitHub URL</Label>
            <Input id="github" placeholder="https://github.com/johndoe" {...register("contact.github")} />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-display text-xl font-semibold text-foreground">Skills <span className="text-destructive">*</span></h3>
        <Controller
          control={control}
          name="skills"
          render={({ field }) => (
            <SkillMultiSelect selected={field.value} onChange={field.onChange} />
          )}
        />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-xl font-semibold text-foreground">Projects <span className="text-destructive">*</span></h3>
          <Button type="button" variant="outline" size="sm" onClick={() => appendProject({ name: "", description: "", link: "", technologies: [] })}>
            <Plus className="mr-1 h-4 w-4" /> Add Project
          </Button>
        </div>
        {projectFields.map((field, index) => (
          <div key={field.id} className="relative rounded-xl border border-border p-4 bg-muted/20 space-y-4">
            {index > 0 && (
              <Button type="button" variant="ghost" size="icon" className="absolute right-2 top-2 text-muted-foreground hover:text-destructive" onClick={() => removeProject(index)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Project Name <span className="text-destructive">*</span></Label>
                <Input placeholder="E-commerce App" {...register(`projects.${index}.name` as const, { required: true })} />
              </div>
              <div className="space-y-1.5">
                <Label>Link / URL</Label>
                <Input placeholder="https://github.com/..." {...register(`projects.${index}.link` as const)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Description</Label>
              <Textarea placeholder="What did you build?" {...register(`projects.${index}.description` as const)} />
            </div>
            <div className="space-y-1.5">
              <Label>Technologies Used</Label>
              <Controller
                control={control}
                name={`projects.${index}.technologies` as const}
                render={({ field: tField }) => (
                  <SkillMultiSelect selected={tField.value || []} onChange={tField.onChange} />
                )}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-xl font-semibold text-foreground">Experience</h3>
          <Button type="button" variant="outline" size="sm" onClick={() => appendExp({ company: "", title: "", start_date: "", end_date: "" })}>
            <Plus className="mr-1 h-4 w-4" /> Add Experience
          </Button>
        </div>
        {expFields.map((field, index) => (
          <div key={field.id} className="relative rounded-xl border border-border p-4 bg-muted/20 space-y-4">
            <Button type="button" variant="ghost" size="icon" className="absolute right-2 top-2 text-muted-foreground hover:text-destructive" onClick={() => removeExp(index)}>
              <Trash2 className="h-4 w-4" />
            </Button>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Company</Label>
                <Input placeholder="Google" {...register(`experience.${index}.company` as const)} />
              </div>
              <div className="space-y-1.5">
                <Label>Job Title</Label>
                <Input placeholder="Software Engineer" {...register(`experience.${index}.title` as const)} />
              </div>
              <div className="space-y-1.5">
                <Label>Start Date</Label>
                <Input placeholder="Jan 2020" {...register(`experience.${index}.start_date` as const)} />
              </div>
              <div className="space-y-1.5">
                <Label>End Date</Label>
                <Input placeholder="Present" {...register(`experience.${index}.end_date` as const)} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-xl font-semibold text-foreground">Education</h3>
          <Button type="button" variant="outline" size="sm" onClick={() => appendEdu({ institution: "", degree: "", field_of_study: "" })}>
            <Plus className="mr-1 h-4 w-4" /> Add Education
          </Button>
        </div>
        {eduFields.map((field, index) => (
          <div key={field.id} className="relative rounded-xl border border-border p-4 bg-muted/20 space-y-4">
            <Button type="button" variant="ghost" size="icon" className="absolute right-2 top-2 text-muted-foreground hover:text-destructive" onClick={() => removeEdu(index)}>
              <Trash2 className="h-4 w-4" />
            </Button>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Institution</Label>
                <Input placeholder="Stanford University" {...register(`education.${index}.institution` as const)} />
              </div>
              <div className="space-y-1.5">
                <Label>Degree</Label>
                <Input placeholder="B.S." {...register(`education.${index}.degree` as const)} />
              </div>
              <div className="space-y-1.5">
                <Label>Field of Study</Label>
                <Input placeholder="Computer Science" {...register(`education.${index}.field_of_study` as const)} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <Button type="submit" disabled={isSubmitting} className="w-full h-12 rounded-full text-base bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm">
        {isSubmitting ? "Saving Profile..." : "Save Profile & Continue"}
      </Button>
    </form>
  );
}
