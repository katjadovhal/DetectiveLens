import { z } from 'zod';

export const selfReportedLevelSchema = z.enum(['beginner', 'somewhat', 'pro']);

export const submitFakePostAnswerSchema = z.object({
  selectedPostId: z.enum(['A', 'B']),
  hintsUsed: z.number().int().min(0).default(0),
  timeSpentMs: z.number().int().min(0).optional(),
});

export const submitFindCluesAnswerSchema = z.object({
  selectedHotspotIds: z.array(z.string()),
  hintsUsed: z.number().int().min(0).default(0),
  timeSpentMs: z.number().int().min(0).optional(),
});

export const submitIsItRealAnswerSchema = z.object({
  selectedAnswer: z.enum(['real', 'ai']),
  hintsUsed: z.number().int().min(0).default(0),
  timeSpentMs: z.number().int().min(0).optional(),
});

export const updateProfileSchema = z.object({
  displayName: z.string().min(1).max(50).optional(),
  avatarId: z.string().optional(),
  selfReportedLevel: selfReportedLevelSchema.optional(),
  settings: z
    .object({
      notifications: z.boolean().optional(),
      sound: z.boolean().optional(),
      privacy: z.boolean().optional(),
    })
    .optional(),
});

export type SubmitFakePostAnswer = z.infer<typeof submitFakePostAnswerSchema>;
export type SubmitFindCluesAnswer = z.infer<typeof submitFindCluesAnswerSchema>;
export type SubmitIsItRealAnswer = z.infer<typeof submitIsItRealAnswerSchema>;
export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;
