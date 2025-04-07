from torch.cuda import is_available

print(f"cuda is { 'available' if is_available() else 'not available'}")
