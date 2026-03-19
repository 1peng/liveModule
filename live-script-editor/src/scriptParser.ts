export class ScriptParser {
    private static readonly OPTION_PATTERN = /\{([^{}]+)\}/g;
    private static readonly SEPARATOR = '|';

    public static parse(text: string): string[][] {
        const options: string[][] = [];
        let match: RegExpExecArray | null;
        let lastIndex = 0;
        
        this.OPTION_PATTERN.lastIndex = 0;
        
        while ((match = this.OPTION_PATTERN.exec(text)) !== null) {
            const optionGroup = match[1];
            const choices = optionGroup.split(this.SEPARATOR).map(s => s.trim());
            options.push(choices);
            lastIndex = match.index + match[0].length;
        }
        
        return options;
    }

    public static generateRandom(text: string): string {
        return text.replace(this.OPTION_PATTERN, (match, group) => {
            const choices = group.split(this.SEPARATOR).map((s: string) => s.trim());
            const randomIndex = Math.floor(Math.random() * choices.length);
            return choices[randomIndex];
        });
    }

    public static generateMultiple(text: string, count: number): string[] {
        const results: string[] = [];
        for (let i = 0; i < count; i++) {
            results.push(this.generateRandom(text));
        }
        return results;
    }

    public static getAllCombinations(text: string): string[] {
        const segments: { type: 'text' | 'option'; content: string | string[] }[] = [];
        let lastIndex = 0;
        let match: RegExpExecArray | null;
        
        const pattern = new RegExp(this.OPTION_PATTERN.source, 'g');
        
        while ((match = pattern.exec(text)) !== null) {
            if (match.index > lastIndex) {
                segments.push({ type: 'text', content: text.slice(lastIndex, match.index) });
            }
            
            const choices = match[1].split(this.SEPARATOR).map(s => s.trim());
            segments.push({ type: 'option', content: choices });
            lastIndex = match.index + match[0].length;
        }
        
        if (lastIndex < text.length) {
            segments.push({ type: 'text', content: text.slice(lastIndex) });
        }
        
        if (segments.length === 0) {
            return [text];
        }
        
        const optionSegments = segments.filter(s => s.type === 'option');
        if (optionSegments.length === 0) {
            return [text];
        }
        
        const totalCombinations = optionSegments.reduce(
            (acc, seg) => acc * (seg.content as string[]).length,
            1
        );
        
        if (totalCombinations > 1000) {
            return this.generateMultiple(text, 1000);
        }
        
        const combinations: string[] = [];
        this.generateCombinationsRecursive(segments, 0, '', combinations);
        return combinations;
    }

    private static generateCombinationsRecursive(
        segments: { type: 'text' | 'option'; content: string | string[] }[],
        index: number,
        current: string,
        results: string[]
    ): void {
        if (index >= segments.length) {
            results.push(current);
            return;
        }
        
        const segment = segments[index];
        
        if (segment.type === 'text') {
            this.generateCombinationsRecursive(
                segments,
                index + 1,
                current + segment.content,
                results
            );
        } else {
            const choices = segment.content as string[];
            for (const choice of choices) {
                this.generateCombinationsRecursive(
                    segments,
                    index + 1,
                    current + choice,
                    results
                );
            }
        }
    }

    public static countCombinations(text: string): number {
        let count = 1;
        let match: RegExpExecArray | null;
        
        this.OPTION_PATTERN.lastIndex = 0;
        
        while ((match = this.OPTION_PATTERN.exec(text)) !== null) {
            const choices = match[1].split(this.SEPARATOR);
            count *= choices.length;
        }
        
        return count;
    }

    public static getOptionGroups(text: string): { match: string; choices: string[]; index: number }[] {
        const groups: { match: string; choices: string[]; index: number }[] = [];
        let match: RegExpExecArray | null;
        
        this.OPTION_PATTERN.lastIndex = 0;
        
        while ((match = this.OPTION_PATTERN.exec(text)) !== null) {
            const choices = match[1].split(this.SEPARATOR).map(s => s.trim());
            groups.push({
                match: match[0],
                choices,
                index: match.index
            });
        }
        
        return groups;
    }
}
