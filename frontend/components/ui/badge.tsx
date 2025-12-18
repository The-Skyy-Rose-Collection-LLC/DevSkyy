/**
 * Badge Component
 * ===============
 * A badge component for displaying status and labels.
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-brand-primary text-white',
        secondary:
          'border-transparent bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100',
        destructive:
          'border-transparent bg-red-500 text-white',
        outline:
          'text-gray-700 dark:text-gray-300',
        success:
          'border-transparent bg-green-500 text-white',
        warning:
          'border-transparent bg-yellow-500 text-white',
        info:
          'border-transparent bg-blue-500 text-white',
        // Agent type badges
        commerce:
          'border-transparent bg-agent-commerce text-white',
        creative:
          'border-transparent bg-agent-creative text-white',
        marketing:
          'border-transparent bg-agent-marketing text-white',
        support:
          'border-transparent bg-agent-support text-white',
        operations:
          'border-transparent bg-agent-operations text-white',
        analytics:
          'border-transparent bg-agent-analytics text-white',
        // LLM provider badges
        anthropic:
          'border-transparent bg-llm-anthropic text-white',
        openai:
          'border-transparent bg-llm-openai text-white',
        google:
          'border-transparent bg-llm-google text-white',
        mistral:
          'border-transparent bg-llm-mistral text-white',
        cohere:
          'border-transparent bg-llm-cohere text-white',
        groq:
          'border-transparent bg-llm-groq text-white',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
