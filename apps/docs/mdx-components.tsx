import defaults from 'fumadocs-ui/mdx';
import { Tab, Tabs } from 'fumadocs-ui/components/tabs';
import { Step, Steps } from 'fumadocs-ui/components/steps';
import type { MDXComponents } from 'mdx/types';
import {
  AxesTable, CatalogCount, CharacterSets, CombinedCss, DownloadTable, FamilyCatalog, FamilyFacts, FamilySpecimen,
  FeatureTable, FontFaceSnippet, GeneratedCode, GlyphBrowserEmbed, InDevelopment, LanguageSupport, OflText,
  ScriptCoverage, Stat, WebFiles,
} from '@/components/docs/family-docs';

export function getMDXComponents(components?: MDXComponents): MDXComponents {
  return {
    ...defaults, Tab, Tabs, Step, Steps,
    AxesTable, CatalogCount, CharacterSets, CombinedCss, DownloadTable, FamilyCatalog, FamilyFacts, FamilySpecimen,
    FeatureTable, FontFaceSnippet, GeneratedCode, GlyphBrowserEmbed, InDevelopment, LanguageSupport, OflText,
    ScriptCoverage, Stat, WebFiles,
    ...components,
  };
}
export const useMDXComponents = getMDXComponents;
