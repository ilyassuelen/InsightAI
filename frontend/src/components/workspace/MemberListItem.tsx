import { WorkspaceMember } from '@/types/workspace';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

interface MemberListItemProps {
  member: WorkspaceMember;
  canRemove: boolean;
  onRemove?: (memberId: string) => void;
  isRemoving?: boolean;
}

export function MemberListItem({
  member,
  canRemove,
  onRemove,
  isRemoving = false
}: MemberListItemProps) {
  const initials = member.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const isOwner = member.role === 'owner';

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-3">
        <Avatar className="h-9 w-9 border border-border">
          <AvatarImage src={member.avatarUrl} alt={member.name} />
          <AvatarFallback className="bg-primary/20 text-primary text-xs font-medium">
            {initials}
          </AvatarFallback>
        </Avatar>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">
              {member.name}
            </span>
            <Badge
              variant={isOwner ? 'default' : 'secondary'}
              className={`text-[10px] px-1.5 py-0 h-4 ${
                isOwner
                  ? 'bg-primary/20 text-primary border-primary/30'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {isOwner ? 'Owner' : 'Member'}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground">
            {member.email}
          </span>
        </div>
      </div>

      {canRemove && !isOwner && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onRemove?.(member.id)}
          disabled={isRemoving}
          className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
          aria-label={`Remove ${member.name}`}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
